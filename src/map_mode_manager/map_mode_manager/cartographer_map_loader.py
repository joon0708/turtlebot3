#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from nav_msgs.msg import OccupancyGrid
from nav_msgs.srv import GetMap
from std_msgs.msg import String
import numpy as np
import yaml
import os
from typing import Optional, Tuple
import time


class CartographerMapLoader(Node):
    """
    기존 맵을 카토그래퍼에 로드하여 이어서 SLAM을 수행하는 노드
    
    - 기존 맵 파일을 로드
    - 카토그래퍼에 맵 데이터 전송
    - 실시간 맵 갱신 지원
    """
    
    def __init__(self):
        super().__init__('cartographer_map_loader')
        
        # QoS 설정
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )
        
        # 파라미터 설정
        self.declare_parameters(
            namespace='',
            parameters=[
                ('map_file_path', '/root/turtlebot3/install/turtlebot3_navigation2/share/turtlebot3_navigation2/map/map.yaml'),
                ('load_existing_map', True),
                ('publish_loaded_map', True),
                ('update_interval', 1.0),
            ]
        )
        
        # 파라미터 로드
        self.map_file_path = self.get_parameter('map_file_path').value
        self.load_existing_map = self.get_parameter('load_existing_map').value
        self.publish_loaded_map = self.get_parameter('publish_loaded_map').value
        self.update_interval = self.get_parameter('update_interval').value
        
        # 발행자
        self.loaded_map_pub = self.create_publisher(OccupancyGrid, '/loaded_map', qos_profile)
        self.status_pub = self.create_publisher(String, '/map_loader_status', qos_profile)
        
        # 상태 변수
        self.loaded_map = None
        self.map_loaded = False
        self.last_update_time = 0.0
        
        # 타이머 설정
        self.update_timer = self.create_timer(self.update_interval, self.publish_loaded_map_periodic)
        
        # 초기 맵 로드
        if self.load_existing_map:
            self.load_map_from_file()
        
        self.get_logger().info('CartographerMapLoader initialized')
        self.publish_status("Map loader started")
    
    def load_map_from_file(self) -> bool:
        """파일에서 맵 로드"""
        try:
            if not os.path.exists(self.map_file_path):
                self.get_logger().error(f'Map file not found: {self.map_file_path}')
                self.publish_status("Map file not found")
                return False
            
            # YAML 파일 읽기
            with open(self.map_file_path, 'r', encoding='utf-8') as file:
                map_data = yaml.safe_load(file)
            
            # 맵 정보 추출
            image_path = map_data['image']
            resolution = float(map_data['resolution'])
            origin = map_data['origin']
            
            # origin을 float 리스트로 변환
            if isinstance(origin, list):
                origin = [float(x) for x in origin]
            else:
                origin = [float(origin[0]), float(origin[1]), float(origin[2]) if len(origin) > 2 else 0.0]
            
            # 이미지 파일 경로 구성
            map_dir = os.path.dirname(self.map_file_path)
            image_full_path = os.path.join(map_dir, image_path)
            
            if not os.path.exists(image_full_path):
                self.get_logger().error(f'Map image file not found: {image_full_path}')
                self.publish_status("Map image file not found")
                return False
            
            # PGM 이미지 로드
            self.loaded_map = self.load_pgm_image(image_full_path, resolution, origin)
            
            if self.loaded_map is not None:
                self.map_loaded = True
                self.get_logger().info(
                    f'Map loaded successfully: {self.loaded_map.info.width}x{self.loaded_map.info.height}, '
                    f'resolution: {resolution}m'
                )
                self.publish_status("Map loaded successfully")
                return True
            else:
                self.get_logger().error('Map load failed')
                self.publish_status("Map load failed")
                return False
                
        except Exception as e:
            self.get_logger().error(f'Error loading map: {e}')
            self.publish_status(f"Map load error: {e}")
            return False
    
    def load_pgm_image(self, image_path: str, resolution: float, origin: list) -> Optional[OccupancyGrid]:
        """PGM 이미지를 OccupancyGrid로 변환"""
        try:
            # PGM 파일 읽기
            with open(image_path, 'rb') as f:
                # PGM 헤더 파싱
                line = f.readline().decode('utf-8').strip()
                if line != 'P5':
                    self.get_logger().error('Not a PGM file format')
                    return None
                
                # 주석 건너뛰기
                while True:
                    line = f.readline().decode('utf-8').strip()
                    if not line.startswith('#'):
                        break
                
                # 너비, 높이 파싱
                width, height = map(int, line.split())
                
                # 최대값 파싱
                max_val = int(f.readline().decode('utf-8').strip())
                
                # 이미지 데이터 읽기
                image_data = f.read()
            
            # OccupancyGrid 메시지 생성
            occupancy_grid = OccupancyGrid()
            occupancy_grid.header.frame_id = 'map'
            occupancy_grid.header.stamp = self.get_clock().now().to_msg()
            
            occupancy_grid.info.resolution = resolution
            occupancy_grid.info.width = width
            occupancy_grid.info.height = height
            
            # 원점 설정
            occupancy_grid.info.origin.position.x = origin[0]
            occupancy_grid.info.origin.position.y = origin[1]
            occupancy_grid.info.origin.position.z = origin[2] if len(origin) > 2 else 0.0
            occupancy_grid.info.origin.orientation.w = 1.0
            
            # 이미지 데이터를 점유도로 변환
            # PGM: 0=검은색(장애물), 254=흰색(자유공간), 205=회색(알 수 없음)
            occupancy_data = []
            unique_pixels = set()
            for pixel in image_data:
                unique_pixels.add(pixel)
                if pixel == 0:  # 검은색 - 장애물
                    occupancy_data.append(100)
                elif pixel >= 250:  # 흰색 - 자유공간 (254, 255 등)
                    occupancy_data.append(0)
                else:  # 회색 - 알 수 없음 (205 등)
                    occupancy_data.append(-1)
            
            # 디버깅: 실제 픽셀 값들 출력
            self.get_logger().info(f'Unique pixel values in PGM: {sorted(unique_pixels)}')
            self.get_logger().info(f'Total pixels: {len(image_data)}, Occupancy data length: {len(occupancy_data)}')
            
            occupancy_grid.data = occupancy_data
            
            return occupancy_grid
            
        except Exception as e:
            self.get_logger().error(f'Error loading PGM image: {e}')
            return None
    
    def publish_loaded_map_periodic(self):
        """주기적으로 로드된 맵 발행"""
        if not self.publish_loaded_map or not self.map_loaded or self.loaded_map is None:
            return
        
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return
        
        # 타임스탬프 업데이트
        self.loaded_map.header.stamp = self.get_clock().now().to_msg()
        
        # 맵 발행
        self.loaded_map_pub.publish(self.loaded_map)
        self.last_update_time = current_time
        
        self.get_logger().debug('Published loaded map')
    
    def publish_status(self, message: str):
        """상태 메시지 발행"""
        status_msg = String()
        status_msg.data = message
        self.status_pub.publish(status_msg)
        self.get_logger().info(message)
    
    def get_loaded_map(self) -> Optional[OccupancyGrid]:
        """로드된 맵 반환"""
        return self.loaded_map
    
    def is_map_loaded(self) -> bool:
        """맵 로드 상태 확인"""
        return self.map_loaded


def main(args=None):
    rclpy.init(args=args)
    node = None
    
    try:
        node = CartographerMapLoader()
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node:
            node.get_logger().info('Keyboard interrupt, shutting down node.')
    except Exception as e:
        if node:
            node.get_logger().error(f'Error during node execution: {e}')
    finally:
        if node:
            try:
                node.destroy_node()
            except Exception as e:
                print(f'Error destroying node: {e}')
        
        if rclpy.ok():
            try:
                rclpy.shutdown()
            except Exception as e:
                print(f'Error shutting down ROS2: {e}')


if __name__ == '__main__':
    main()
