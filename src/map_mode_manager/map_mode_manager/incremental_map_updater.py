#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from nav_msgs.msg import OccupancyGrid
from std_msgs.msg import String, Bool
import numpy as np
import cv2
from typing import Optional, List, Tuple
import time
import os
import shutil
from datetime import datetime


class IncrementalMapUpdater(Node):
    """
    점진적 맵 업데이트를 담당하는 노드
    
    - 통합된 맵을 기존 맵 파일에 점진적으로 적용
    - 백업 및 롤백 기능 제공
    - 맵 업데이트 이력 관리
    """
    
    def __init__(self):
        super().__init__('incremental_map_updater')
        
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
                ('base_map_path', '/root/turtlebot3/install/turtlebot3_navigation2/share/turtlebot3_navigation2/map'),
                ('backup_enabled', True),
                ('max_backups', 10),
                ('update_confidence_threshold', 0.8),
                ('min_update_interval', 30.0),  # 최소 업데이트 간격 (초)
                ('auto_update_enabled', True),
            ]
        )
        
        # 파라미터 로드
        self.base_map_path = self.get_parameter('base_map_path').value
        self.backup_enabled = self.get_parameter('backup_enabled').value
        self.max_backups = self.get_parameter('max_backups').value
        self.update_confidence_threshold = self.get_parameter('update_confidence_threshold').value
        self.min_update_interval = self.get_parameter('min_update_interval').value
        self.auto_update_enabled = self.get_parameter('auto_update_enabled').value
        
        # 구독자
        self.fused_map_sub = self.create_subscription(
            OccupancyGrid, '/fused_map', self.fused_map_callback, qos_profile
        )
        self.update_request_sub = self.create_subscription(
            Bool, '/map_update_request', self.update_request_callback, qos_profile
        )
        
        # 발행자
        self.update_status_pub = self.create_publisher(String, '/map_update_status', qos_profile)
        self.update_result_pub = self.create_publisher(Bool, '/map_update_result', qos_profile)
        
        # 상태 변수
        self.latest_fused_map = None
        self.last_update_time = 0.0
        self.update_count = 0
        self.backup_count = 0
        
        # 백업 디렉토리 생성
        self.backup_dir = os.path.join(self.base_map_path, 'backups')
        if self.backup_enabled:
            os.makedirs(self.backup_dir, exist_ok=True)
        
        self.get_logger().info(
            f'IncrementalMapUpdater 초기화 완료. '
            f'기본 맵 경로: {self.base_map_path}, '
            f'백업 활성화: {self.backup_enabled}'
        )
    
    def fused_map_callback(self, msg: OccupancyGrid):
        """통합된 맵 콜백"""
        self.latest_fused_map = msg
        self.get_logger().debug('통합된 맵 수신')
        
        # 자동 업데이트가 활성화된 경우
        if self.auto_update_enabled:
            self.check_auto_update()
    
    def update_request_callback(self, msg: Bool):
        """맵 업데이트 요청 콜백"""
        if msg.data and self.latest_fused_map is not None:
            self.get_logger().info('맵 업데이트 요청 수신')
            self.perform_map_update()
    
    def check_auto_update(self):
        """자동 업데이트 조건 확인"""
        current_time = time.time()
        
        # 최소 업데이트 간격 확인
        if current_time - self.last_update_time < self.min_update_interval:
            return
        
        # 통합된 맵이 있는지 확인
        if self.latest_fused_map is None:
            return
        
        # 자동 업데이트 수행
        self.perform_map_update()
    
    def create_backup(self) -> bool:
        """현재 맵 파일 백업"""
        if not self.backup_enabled:
            return True
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"map_backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # 맵 파일들 백업
            map_files = ['map.yaml', 'map.pgm']
            for file_name in map_files:
                source_path = os.path.join(self.base_map_path, file_name)
                if os.path.exists(source_path):
                    dest_path = os.path.join(backup_path, file_name)
                    os.makedirs(backup_path, exist_ok=True)
                    shutil.copy2(source_path, dest_path)
            
            self.backup_count += 1
            self.get_logger().info(f'맵 백업 완료: {backup_name}')
            
            # 오래된 백업 삭제
            self.cleanup_old_backups()
            
            return True
            
        except Exception as e:
            self.get_logger().error(f'백업 생성 실패: {e}')
            return False
    
    def cleanup_old_backups(self):
        """오래된 백업 파일 정리"""
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            # 백업 디렉토리 목록 가져오기
            backup_dirs = []
            for item in os.listdir(self.backup_dir):
                item_path = os.path.join(self.backup_dir, item)
                if os.path.isdir(item_path) and item.startswith('map_backup_'):
                    backup_dirs.append((item, os.path.getmtime(item_path)))
            
            # 수정 시간 기준으로 정렬
            backup_dirs.sort(key=lambda x: x[1], reverse=True)
            
            # 최대 백업 수를 초과하는 경우 오래된 것 삭제
            if len(backup_dirs) > self.max_backups:
                for backup_name, _ in backup_dirs[self.max_backups:]:
                    backup_path = os.path.join(self.backup_dir, backup_name)
                    shutil.rmtree(backup_path)
                    self.get_logger().info(f'오래된 백업 삭제: {backup_name}')
                    
        except Exception as e:
            self.get_logger().error(f'백업 정리 실패: {e}')
    
    def occupancy_grid_to_pgm(self, grid: OccupancyGrid) -> np.ndarray:
        """OccupancyGrid를 PGM 형식으로 변환"""
        # -1: 알 수 없음, 0: 자유 공간, 100: 장애물
        data = np.array(grid.data, dtype=np.int8)
        data = data.reshape((grid.info.height, grid.info.width))
        
        # PGM 형식으로 변환: 0-255 범위
        pgm_data = np.zeros_like(data, dtype=np.uint8)
        pgm_data[data == -1] = 205  # 알 수 없음 (회색)
        pgm_data[data == 0] = 254   # 자유 공간 (밝은 회색)
        pgm_data[data == 100] = 0   # 장애물 (검은색)
        
        return pgm_data
    
    def update_map_yaml(self, grid: OccupancyGrid) -> str:
        """맵 YAML 파일 내용 생성"""
        yaml_content = f"""image: map.pgm
resolution: {grid.info.resolution}
origin: [{grid.info.origin.position.x}, {grid.info.origin.position.y}, {grid.info.origin.position.z}]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
"""
        return yaml_content
    
    def save_pgm_file(self, pgm_data: np.ndarray, file_path: str) -> bool:
        """PGM 파일 저장"""
        try:
            height, width = pgm_data.shape
            
            with open(file_path, 'wb') as f:
                # PGM 헤더 작성
                f.write(f'P5\n{width} {height}\n255\n'.encode())
                # 이미지 데이터 작성
                f.write(pgm_data.tobytes())
            
            return True
            
        except Exception as e:
            self.get_logger().error(f'PGM 파일 저장 실패: {e}')
            return False
    
    def perform_map_update(self) -> bool:
        """맵 업데이트 수행"""
        if self.latest_fused_map is None:
            self.get_logger().warn('업데이트할 통합 맵이 없습니다.')
            return False
        
        try:
            # 백업 생성
            if not self.create_backup():
                self.get_logger().error('백업 생성 실패로 업데이트를 중단합니다.')
                return False
            
            # 통합된 맵을 PGM 형식으로 변환
            pgm_data = self.occupancy_grid_to_pgm(self.latest_fused_map)
            
            # PGM 파일 저장
            pgm_path = os.path.join(self.base_map_path, 'map.pgm')
            if not self.save_pgm_file(pgm_data, pgm_path):
                return False
            
            # YAML 파일 업데이트
            yaml_content = self.update_map_yaml(self.latest_fused_map)
            yaml_path = os.path.join(self.base_map_path, 'map.yaml')
            
            with open(yaml_path, 'w') as f:
                f.write(yaml_content)
            
            # 업데이트 완료
            self.update_count += 1
            self.last_update_time = time.time()
            
            self.get_logger().info(
                f'맵 업데이트 완료: {self.latest_fused_map.info.width}x{self.latest_fused_map.info.height}, '
                f'업데이트 횟수: {self.update_count}'
            )
            
            # 상태 발행
            self.publish_update_status(True, f'업데이트 완료 (횟수: {self.update_count})')
            
            return True
            
        except Exception as e:
            self.get_logger().error(f'맵 업데이트 실패: {e}')
            self.publish_update_status(False, f'업데이트 실패: {e}')
            return False
    
    def publish_update_status(self, success: bool, message: str):
        """업데이트 상태 발행"""
        # 상태 메시지 발행
        status_msg = String()
        status_msg.data = message
        self.update_status_pub.publish(status_msg)
        
        # 결과 발행
        result_msg = Bool()
        result_msg.data = success
        self.update_result_pub.publish(result_msg)
    
    def rollback_to_backup(self, backup_name: str) -> bool:
        """백업으로 롤백"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            if not os.path.exists(backup_path):
                self.get_logger().error(f'백업을 찾을 수 없습니다: {backup_name}')
                return False
            
            # 백업 파일들을 기본 맵 경로로 복원
            map_files = ['map.yaml', 'map.pgm']
            for file_name in map_files:
                source_path = os.path.join(backup_path, file_name)
                if os.path.exists(source_path):
                    dest_path = os.path.join(self.base_map_path, file_name)
                    shutil.copy2(source_path, dest_path)
            
            self.get_logger().info(f'백업으로 롤백 완료: {backup_name}')
            return True
            
        except Exception as e:
            self.get_logger().error(f'롤백 실패: {e}')
            return False
    
    def get_update_statistics(self) -> dict:
        """업데이트 통계 반환"""
        return {
            'update_count': self.update_count,
            'backup_count': self.backup_count,
            'last_update_time': self.last_update_time,
            'auto_update_enabled': self.auto_update_enabled,
            'backup_enabled': self.backup_enabled
        }


def main(args=None):
    rclpy.init(args=args)
    node = None
    
    try:
        node = IncrementalMapUpdater()
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
