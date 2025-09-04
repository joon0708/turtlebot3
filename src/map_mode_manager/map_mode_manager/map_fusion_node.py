#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from nav_msgs.msg import OccupancyGrid
from std_msgs.msg import Float32, String, Bool
import numpy as np
import cv2
from typing import Optional, Tuple, List
import time
import os


class MapFusionNode(Node):
    """
    기존 맵과 실시간 맵을 비교하고 통합하는 노드
    
    - 기존 맵 (Navigation2): 안정적인 네비게이션용
    - 실시간 맵 (카토그래퍼): 환경 변화 감지용
    - 두 맵을 비교하여 변화 영역을 감지하고 점진적으로 통합
    """
    
    def __init__(self):
        super().__init__('map_fusion_node')
        
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
                ('change_threshold', 0.3),           # 변화 감지 임계값
                ('fusion_confidence', 0.8),          # 통합 신뢰도 임계값
                ('update_interval', 2.0),            # 업데이트 주기 (초)
                ('min_change_area', 50),             # 최소 변화 영역 크기 (픽셀)
                ('enable_incremental_update', True), # 점진적 업데이트 활성화
            ]
        )
        
        # 파라미터 로드
        self.change_threshold = self.get_parameter('change_threshold').value
        self.fusion_confidence = self.get_parameter('fusion_confidence').value
        self.update_interval = self.get_parameter('update_interval').value
        self.min_change_area = self.get_parameter('min_change_area').value
        self.enable_incremental_update = self.get_parameter('enable_incremental_update').value
        
        # 구독자
        self.base_map_sub = self.create_subscription(
            OccupancyGrid, '/map', self.base_map_callback, qos_profile
        )
        self.realtime_map_sub = self.create_subscription(
            OccupancyGrid, '/cartographer_map', self.realtime_map_callback, qos_profile
        )
        
        # 발행자
        self.fused_map_pub = self.create_publisher(OccupancyGrid, '/fused_map', qos_profile)
        self.change_detected_pub = self.create_publisher(Bool, '/map_change_detected', qos_profile)
        self.fusion_status_pub = self.create_publisher(String, '/fusion_status', qos_profile)
        self.similarity_score_pub = self.create_publisher(Float32, '/map_similarity_score', qos_profile)
        
        # 상태 변수
        self.base_map = None
        self.realtime_map = None
        self.fused_map = None
        self.last_fusion_time = 0.0
        self.fusion_count = 0
        self.change_count = 0
        
        # 타이머 설정
        self.fusion_timer = self.create_timer(self.update_interval, self.perform_fusion)
        
        self.get_logger().info(
            f'MapFusionNode 초기화 완료. '
            f'변화 임계값: {self.change_threshold}, '
            f'업데이트 주기: {self.update_interval}초'
        )
    
    def base_map_callback(self, msg: OccupancyGrid):
        """기존 맵 콜백 (Navigation2)"""
        self.base_map = msg
        self.get_logger().debug(f'기존 맵 수신: {msg.info.width}x{msg.info.height}')
    
    def realtime_map_callback(self, msg: OccupancyGrid):
        """실시간 맵 콜백 (카토그래퍼)"""
        self.realtime_map = msg
        self.get_logger().debug(f'실시간 맵 수신: {msg.info.width}x{msg.info.height}')
    
    def occupancy_grid_to_image(self, grid: OccupancyGrid) -> np.ndarray:
        """OccupancyGrid를 OpenCV 이미지로 변환"""
        # -1: 알 수 없음, 0: 자유 공간, 100: 장애물
        data = np.array(grid.data, dtype=np.int8)
        data = data.reshape((grid.info.height, grid.info.width))
        
        # 정규화: -1,0,100 -> 0,128,255
        image = np.zeros_like(data, dtype=np.uint8)
        image[data == -1] = 128  # 알 수 없음 (회색)
        image[data == 0] = 0     # 자유 공간 (검은색)
        image[data == 100] = 255 # 장애물 (흰색)
        
        return image
    
    def image_to_occupancy_grid(self, image: np.ndarray, grid_info) -> List[int]:
        """OpenCV 이미지를 OccupancyGrid 데이터로 변환"""
        data = []
        for row in image:
            for pixel in row:
                if pixel == 128:    # 회색 -> 알 수 없음
                    data.append(-1)
                elif pixel == 0:    # 검은색 -> 자유 공간
                    data.append(0)
                elif pixel == 255:  # 흰색 -> 장애물
                    data.append(100)
                else:               # 기타 -> 알 수 없음
                    data.append(-1)
        return data
    
    def resize_maps_to_match(self, map1: np.ndarray, map2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """두 맵을 같은 크기로 리사이즈"""
        # 더 큰 맵의 크기에 맞춤
        h1, w1 = map1.shape
        h2, w2 = map2.shape
        
        target_h = max(h1, h2)
        target_w = max(w1, w2)
        
        # 리사이즈
        map1_resized = cv2.resize(map1, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
        map2_resized = cv2.resize(map2, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
        
        return map1_resized, map2_resized
    
    def calculate_map_similarity(self, map1: np.ndarray, map2: np.ndarray) -> float:
        """두 맵의 유사도 계산"""
        # 알 수 없는 영역 제외하고 비교
        mask1 = (map1 != 128)  # 알 수 없음이 아닌 영역
        mask2 = (map2 != 128)
        valid_mask = mask1 & mask2
        
        if np.sum(valid_mask) == 0:
            return 0.0
        
        # 유효한 픽셀에서 일치하는 픽셀 비율 계산
        matches = (map1[valid_mask] == map2[valid_mask])
        similarity = np.sum(matches) / np.sum(valid_mask)
        
        return float(similarity)
    
    def detect_changes(self, map1: np.ndarray, map2: np.ndarray) -> Tuple[np.ndarray, int]:
        """맵 변화 영역 감지"""
        # 알 수 없는 영역 제외
        mask1 = (map1 != 128)
        mask2 = (map2 != 128)
        valid_mask = mask1 & mask2
        
        # 변화 영역 계산
        changes = np.zeros_like(map1, dtype=np.uint8)
        changes[valid_mask] = (map1[valid_mask] != map2[valid_mask]).astype(np.uint8) * 255
        
        # 모폴로지 연산으로 노이즈 제거
        kernel = np.ones((3, 3), np.uint8)
        changes = cv2.morphologyEx(changes, cv2.MORPH_CLOSE, kernel)
        changes = cv2.morphologyEx(changes, cv2.MORPH_OPEN, kernel)
        
        # 변화 영역 크기 계산
        change_area = np.sum(changes > 0)
        
        return changes, change_area
    
    def fuse_maps(self, base_map: np.ndarray, realtime_map: np.ndarray, 
                  changes: np.ndarray) -> np.ndarray:
        """두 맵을 통합"""
        fused_map = base_map.copy()
        
        # 변화 영역에서만 실시간 맵의 정보를 사용
        change_mask = changes > 0
        
        # 신뢰도가 높은 영역만 통합
        if self.enable_incremental_update:
            # 점진적 업데이트: 변화 영역의 일부만 통합
            confidence_mask = np.random.random(fused_map.shape) < self.fusion_confidence
            update_mask = change_mask & confidence_mask
        else:
            # 전체 변화 영역 통합
            update_mask = change_mask
        
        fused_map[update_mask] = realtime_map[update_mask]
        
        return fused_map
    
    def perform_fusion(self):
        """맵 통합 수행"""
        if self.base_map is None or self.realtime_map is None:
            return
        
        current_time = time.time()
        if current_time - self.last_fusion_time < self.update_interval:
            return
        
        try:
            # 맵을 이미지로 변환
            base_image = self.occupancy_grid_to_image(self.base_map)
            realtime_image = self.occupancy_grid_to_image(self.realtime_map)
            
            # 좌표계 변환: 실시간 맵을 기존 맵의 좌표계에 맞춤
            base_origin_x = self.base_map.info.origin.position.x
            base_origin_y = self.base_map.info.origin.position.y
            realtime_origin_x = self.realtime_map.info.origin.position.x
            realtime_origin_y = self.realtime_map.info.origin.position.y
            
            # 원점 차이 계산
            origin_diff_x = base_origin_x - realtime_origin_x
            origin_diff_y = base_origin_y - realtime_origin_y
            
            # 픽셀 단위로 변환
            resolution = self.base_map.info.resolution
            pixel_diff_x = int(origin_diff_x / resolution)
            pixel_diff_y = int(origin_diff_y / resolution)
            
            # 실시간 맵을 기존 맵 좌표계로 변환
            if pixel_diff_x != 0 or pixel_diff_y != 0:
                # 이미지 변환 (이동)
                rows, cols = realtime_image.shape
                M = np.float32([[1, 0, pixel_diff_x], [0, 1, pixel_diff_y]])
                realtime_image = cv2.warpAffine(realtime_image, M, (cols, rows))
                self.get_logger().info(f'좌표계 변환 적용: x={pixel_diff_x}, y={pixel_diff_y}')
            
            # 맵 크기 맞추기
            base_image, realtime_image = self.resize_maps_to_match(base_image, realtime_image)
            
            # 유사도 계산
            similarity = self.calculate_map_similarity(base_image, realtime_image)
            
            # 변화 감지
            changes, change_area = self.detect_changes(base_image, realtime_image)
            
            # 변화 감지 여부 판단
            change_detected = change_area > self.min_change_area
            
            # 맵 통합
            if change_detected:
                fused_image = self.fuse_maps(base_image, realtime_image, changes)
                
                # 통합된 맵을 OccupancyGrid로 변환
                fused_grid = OccupancyGrid()
                fused_grid.header = self.base_map.header
                fused_grid.info = self.base_map.info
                fused_grid.info.width = fused_image.shape[1]
                fused_grid.info.height = fused_image.shape[0]
                fused_grid.data = self.image_to_occupancy_grid(fused_image, fused_grid.info)
                
                # 통합된 맵 발행
                self.fused_map_pub.publish(fused_grid)
                self.fused_map = fused_grid
                self.fusion_count += 1
                
                self.get_logger().info(
                    f'맵 통합 완료: 유사도 {similarity:.3f}, '
                    f'변화 영역 {change_area} 픽셀, '
                    f'통합 횟수 {self.fusion_count}'
                )
            else:
                # 변화가 없으면 기존 맵 그대로 사용
                self.fused_map_pub.publish(self.base_map)
                self.fused_map = self.base_map
            
            # 상태 발행
            self.publish_status(similarity, change_detected, change_area)
            
            self.last_fusion_time = current_time
            
        except Exception as e:
            self.get_logger().error(f'맵 통합 중 오류: {e}')
    
    def publish_status(self, similarity: float, change_detected: bool, change_area: int):
        """상태 정보 발행"""
        # 유사도 점수 발행
        similarity_msg = Float32()
        similarity_msg.data = similarity
        self.similarity_score_pub.publish(similarity_msg)
        
        # 변화 감지 상태 발행
        change_msg = Bool()
        change_msg.data = change_detected
        self.change_detected_pub.publish(change_msg)
        
        # 통합 상태 발행
        status_msg = String()
        if change_detected:
            status_msg.data = f'CHANGE_DETECTED:similarity={similarity:.3f},area={change_area}'
            self.change_count += 1
        else:
            status_msg.data = f'STABLE:similarity={similarity:.3f}'
        
        self.fusion_status_pub.publish(status_msg)
    
    def get_fusion_statistics(self) -> dict:
        """통합 통계 반환"""
        return {
            'fusion_count': self.fusion_count,
            'change_count': self.change_count,
            'last_fusion_time': self.last_fusion_time,
            'base_map_available': self.base_map is not None,
            'realtime_map_available': self.realtime_map is not None
        }


def main(args=None):
    rclpy.init(args=args)
    node = None
    
    try:
        node = MapFusionNode()
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
