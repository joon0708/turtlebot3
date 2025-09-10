#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32
import numpy as np
import math
from typing import Tuple, List, Optional
import tf2_ros
from tf2_ros import TransformException


class MapComparator(Node):
    """
    맵 비교 알고리즘을 담당하는 노드
    
    현재 LiDAR 스캔과 기존 맵을 비교하여 유사도를 계산합니다.
    """
    
    def __init__(self):
        super().__init__('map_comparator')
        
        # QoS 설정 (호환성 향상)
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )
        
        # 파라미터 설정
        self.declare_parameters(
            namespace='',
            parameters=[
                ('scan_sampling_ratio', 0.1),      # 스캔 데이터 샘플링 비율
                ('map_resolution', 0.05),          # 맵 해상도 (미터)
                ('comparison_area_size', 5.0),     # 비교 영역 크기 (미터)
                ('min_scan_points', 10),           # 최소 스캔 포인트 수
                ('max_scan_range', 3.5),           # 최대 스캔 범위 (미터)
            ]
        )
        
        # 파라미터 로드
        self.scan_sampling_ratio = self.get_parameter('scan_sampling_ratio').value
        self.map_resolution = self.get_parameter('map_resolution').value
        self.comparison_area_size = self.get_parameter('comparison_area_size').value
        self.min_scan_points = self.get_parameter('min_scan_points').value
        self.max_scan_range = self.get_parameter('max_scan_range').value
        
        # 구독자 및 발행자
        self.scan_sub = self.create_subscription(
            LaserScan, 'scan', self.scan_callback, qos_profile
        )
        self.map_sub = self.create_subscription(
            OccupancyGrid, 'map', self.map_callback, qos_profile
        )
        
        # 유사도 점수 발행자
        self.similarity_pub = self.create_publisher(Float32, 'map_similarity_score', qos_profile)
        
        # TF 리스너
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # 상태 변수
        self.current_scan = None
        self.current_map = None
        self.robot_pose = None
        self.last_comparison_time = None
        self.last_similarity_score = 0.0
        
        # 타이머 설정 (1초마다 맵 비교)
        self.comparison_timer = self.create_timer(1.0, self.perform_comparison)
        
        self.get_logger().info('MapComparator node initialized.')
    
    def scan_callback(self, msg: LaserScan):
        """LiDAR 스캔 데이터 콜백"""
        self.current_scan = msg
        self.get_logger().debug(f'새로운 스캔 데이터 수신: {len(msg.ranges)} 포인트')
    
    def map_callback(self, msg: OccupancyGrid):
        """맵 데이터 콜백"""
        self.current_map = msg
        self.get_logger().debug(f'새로운 맵 데이터 수신: {msg.info.width}x{msg.info.height}')
    
    def get_robot_pose(self) -> Optional[PoseStamped]:
        """현재 로봇의 위치를 가져옵니다."""
        try:
            # base_link에서 map으로의 변환 가져오기
            transform = self.tf_buffer.lookup_transform(
                'map', 'base_link', rclpy.time.Time()
            )
            
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position.x = transform.transform.translation.x
            pose.pose.position.y = transform.transform.translation.y
            pose.pose.orientation = transform.transform.rotation
            
            return pose
            
        except TransformException as e:
            self.get_logger().warn(f'TF 변환 실패: {e}')
            return None
    
    def sample_scan_data(self, scan: LaserScan) -> List[Tuple[float, float]]:
        """스캔 데이터를 샘플링합니다."""
        if not scan.ranges:
            return []
        
        # 유효한 범위 데이터만 필터링
        valid_ranges = []
        for i, range_val in enumerate(scan.ranges):
            if (scan.range_min <= range_val <= scan.range_max and 
                range_val <= self.max_scan_range):
                
                # 각도 계산
                angle = scan.angle_min + i * scan.angle_increment
                
                # 직교 좌표로 변환
                x = range_val * math.cos(angle)
                y = range_val * math.sin(angle)
                
                valid_ranges.append((x, y))
        
        # 샘플링
        if len(valid_ranges) > self.min_scan_points:
            sample_size = max(self.min_scan_points, 
                            int(len(valid_ranges) * self.scan_sampling_ratio))
            indices = np.linspace(0, len(valid_ranges) - 1, sample_size, dtype=int)
            sampled_ranges = [valid_ranges[i] for i in indices]
        else:
            sampled_ranges = valid_ranges
        
        return sampled_ranges
    
    def map_to_world_coordinates(self, map_x: int, map_y: int, map_info) -> Tuple[float, float]:
        """맵 좌표를 월드 좌표로 변환합니다."""
        world_x = map_info.origin.position.x + map_x * map_info.resolution
        world_y = map_info.origin.position.y + map_y * map_info.resolution
        return world_x, world_y
    
    def world_to_map_coordinates(self, world_x: float, world_y: float, map_info) -> Tuple[int, int]:
        """월드 좌표를 맵 좌표로 변환합니다."""
        map_x = int((world_x - map_info.origin.position.x) / map_info.resolution)
        map_y = int((world_y - map_info.origin.position.y) / map_info.resolution)
        return map_x, map_y
    
    def get_map_occupancy_around_robot(self, robot_pose: PoseStamped, 
                                     area_size: float) -> List[Tuple[float, float, int]]:
        """로봇 주변의 맵 점유 상태를 가져옵니다."""
        if not self.current_map:
            return []
        
        map_info = self.current_map.info
        robot_x = robot_pose.pose.position.x
        robot_y = robot_pose.pose.position.y
        
        # 비교 영역 계산
        half_size = area_size / 2.0
        min_x = robot_x - half_size
        max_x = robot_x + half_size
        min_y = robot_y - half_size
        max_y = robot_y + half_size
        
        # 맵 좌표로 변환
        min_map_x, min_map_y = self.world_to_map_coordinates(min_x, min_y, map_info)
        max_map_x, max_map_y = self.world_to_map_coordinates(max_x, max_y, map_info)
        
        # 맵 경계 확인
        min_map_x = max(0, min_map_x)
        min_map_y = max(0, min_map_y)
        max_map_x = min(map_info.width - 1, max_map_x)
        max_map_y = min(map_info.height - 1, max_map_y)
        
        # 점유 상태 수집
        occupancy_data = []
        for map_x in range(min_map_x, max_map_x + 1):
            for map_y in range(min_map_y, max_map_y + 1):
                # 맵 인덱스 계산
                map_index = map_y * map_info.width + map_x
                if 0 <= map_index < len(self.current_map.data):
                    occupancy = self.current_map.data[map_index]
                    
                    # 월드 좌표로 변환
                    world_x, world_y = self.map_to_world_coordinates(map_x, map_y, map_info)
                    
                    # 로봇 기준 상대 좌표로 변환
                    rel_x = world_x - robot_x
                    rel_y = world_y - robot_y
                    
                    occupancy_data.append((rel_x, rel_y, occupancy))
        
        return occupancy_data
    
    def compare_scan_with_map(self, scan_points: List[Tuple[float, float]], 
                             map_occupancy: List[Tuple[float, float, int]]) -> float:
        """스캔 데이터와 맵 점유 상태를 비교합니다."""
        if not scan_points or not map_occupancy:
            return 0.0
        
        # 맵 점유 상태를 그리드로 변환
        grid_size = int(self.comparison_area_size / self.map_resolution)
        grid = np.zeros((grid_size, grid_size), dtype=np.int8)
        
        # 맵 데이터를 그리드에 배치
        for rel_x, rel_y, occupancy in map_occupancy:
            grid_x = int((rel_x + self.comparison_area_size / 2) / self.map_resolution)
            grid_y = int((rel_y + self.comparison_area_size / 2) / self.map_resolution)
            
            if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                grid[grid_y, grid_x] = occupancy
        
        # 스캔 포인트와 맵 비교
        matches = 0
        total_points = len(scan_points)
        
        for scan_x, scan_y in scan_points:
            # 스캔 포인트를 그리드 좌표로 변환
            grid_x = int((scan_x + self.comparison_area_size / 2) / self.map_resolution)
            grid_y = int((scan_y + self.comparison_area_size / 2) / self.map_resolution)
            
            if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                map_occupancy = grid[grid_y, grid_x]
                
                # 점유 상태가 일치하는지 확인
                # 0: 자유 공간, 100: 장애물, -1: 알 수 없음
                if map_occupancy >= 50:  # 장애물 영역
                    # 스캔에서 장애물이 감지된 경우
                    if abs(scan_x) < self.max_scan_range and abs(scan_y) < self.max_scan_range:
                        matches += 1
                elif map_occupancy == 0:  # 자유 공간
                    # 스캔에서 자유 공간이 감지된 경우
                    if abs(scan_x) >= self.max_scan_range or abs(scan_y) >= self.max_scan_range:
                        matches += 1
        
        # 유사도 점수 계산 (0.0 ~ 1.0)
        if total_points > 0:
            similarity = matches / total_points
        else:
            similarity = 0.0
        
        return similarity
    
    def perform_comparison(self):
        """주기적으로 맵 비교를 수행합니다."""
        if not self.current_scan or not self.current_map:
            return
        
        # 로봇 위치 가져오기
        robot_pose = self.get_robot_pose()
        if not robot_pose:
            return
        
        # 스캔 데이터 샘플링
        sampled_scan = self.sample_scan_data(self.current_scan)
        if len(sampled_scan) < self.min_scan_points:
            self.get_logger().warn(f'스캔 데이터 부족: {len(sampled_scan)} < {self.min_scan_points}')
            return
        
        # 맵 점유 상태 가져오기
        map_occupancy = self.get_map_occupancy_around_robot(robot_pose, self.comparison_area_size)
        
        # 맵 비교 수행
        similarity_score = self.compare_scan_with_map(sampled_scan, map_occupancy)
        
        # 결과 로깅
        self.get_logger().info(
            f'맵 유사도: {similarity_score:.3f} '
            f'(스캔: {len(sampled_scan)} 포인트, '
            f'맵: {len(map_occupancy)} 셀)'
        )
        
        # 유사도 점수 발행
        similarity_msg = Float32()
        similarity_msg.data = similarity_score
        self.similarity_pub.publish(similarity_msg)
        
        # 최근 유사도 점수 저장
        self.last_similarity_score = similarity_score
        
        self.last_comparison_time = self.get_clock().now()
    
    def get_similarity_score(self) -> float:
        """최근 유사도 점수를 반환합니다."""
        return self.last_similarity_score


def main(args=None):
    rclpy.init(args=args)
    node = None
    
    try:
        node = MapComparator()
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node:
            node.get_logger().info('키보드 인터럽트로 노드를 종료합니다.')
    except Exception as e:
        if node:
            node.get_logger().error(f'노드 실행 중 오류 발생: {e}')
    finally:
        if node:
            try:
                node.destroy_node()
            except Exception as e:
                print(f'노드 파괴 중 오류: {e}')
        
        if rclpy.ok():
            try:
                rclpy.shutdown()
            except Exception as e:
                print(f'ROS2 종료 중 오류: {e}')


if __name__ == '__main__':
    main()
