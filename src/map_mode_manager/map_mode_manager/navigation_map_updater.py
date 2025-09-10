#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from nav_msgs.msg import OccupancyGrid, Path
from geometry_msgs.msg import PoseStamped, Twist
from std_msgs.msg import String, Bool
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
import numpy as np
import time
import os
from typing import Optional, List, Tuple
from datetime import datetime


class NavigationMapUpdater(Node):
    """
    네비게이션 중 실시간 맵 갱신을 담당하는 노드
    
    - 네비게이션 상태 모니터링
    - 로봇 이동 중 새로운 영역 탐지
    - 실시간 맵 업데이트 트리거
    - 맵 갱신 상태 관리
    """
    
    def __init__(self):
        super().__init__('navigation_map_updater')
        
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
                ('update_interval', 5.0),              # 맵 업데이트 간격 (초)
                ('min_movement_distance', 1.0),        # 최소 이동 거리 (미터)
                ('exploration_threshold', 0.3),        # 탐험 임계값 (새로운 영역 비율)
                ('auto_update_enabled', True),         # 자동 업데이트 활성화
                ('update_during_navigation', True),    # 네비게이션 중 업데이트
                ('map_confidence_threshold', 0.7),     # 맵 신뢰도 임계값
            ]
        )
        
        # 파라미터 로드
        self.update_interval = self.get_parameter('update_interval').value
        self.min_movement_distance = self.get_parameter('min_movement_distance').value
        self.exploration_threshold = self.get_parameter('exploration_threshold').value
        self.auto_update_enabled = self.get_parameter('auto_update_enabled').value
        self.update_during_navigation = self.get_parameter('update_during_navigation').value
        self.map_confidence_threshold = self.get_parameter('map_confidence_threshold').value
        
        # 구독자
        self.map_sub = self.create_subscription(
            OccupancyGrid, '/map', self.map_callback, qos_profile
        )
        self.robot_pose_sub = self.create_subscription(
            PoseStamped, '/robot_pose', self.robot_pose_callback, qos_profile
        )
        self.cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, qos_profile
        )
        self.nav_goal_sub = self.create_subscription(
            PoseStamped, '/goal_pose', self.nav_goal_callback, qos_profile
        )
        
        # 발행자
        self.map_update_request_pub = self.create_publisher(
            Bool, '/map_update_request', qos_profile
        )
        self.update_status_pub = self.create_publisher(
            String, '/navigation_map_update_status', qos_profile
        )
        self.exploration_status_pub = self.create_publisher(
            String, '/exploration_status', qos_profile
        )
        
        # Action Client (네비게이션 상태 확인용)
        self.nav_action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # 상태 변수
        self.current_map = None
        self.previous_map = None
        self.robot_pose = None
        self.previous_pose = None
        self.is_navigating = False
        self.is_moving = False
        self.last_update_time = 0.0
        self.last_pose_time = 0.0
        self.total_distance_moved = 0.0
        self.explored_area_ratio = 0.0
        self.update_count = 0
        
        # 타이머 설정
        self.update_timer = self.create_timer(self.update_interval, self.check_map_update)
        self.status_timer = self.create_timer(2.0, self.publish_status)
        
        self.get_logger().info(
            f'NavigationMapUpdater 초기화 완료. '
            f'업데이트 간격: {self.update_interval}초, '
            f'자동 업데이트: {self.auto_update_enabled}'
        )
        self.publish_status_message("네비게이션 맵 업데이터 시작됨")
    
    def map_callback(self, msg: OccupancyGrid):
        """맵 데이터 콜백"""
        self.previous_map = self.current_map
        self.current_map = msg
        self.get_logger().debug(f'새로운 맵 데이터 수신: {msg.info.width}x{msg.info.height}')
    
    def robot_pose_callback(self, msg: PoseStamped):
        """로봇 위치 콜백"""
        self.previous_pose = self.robot_pose
        self.robot_pose = msg
        self.last_pose_time = time.time()
        
        # 이동 거리 계산
        if self.previous_pose is not None:
            distance = self.calculate_distance(self.previous_pose, self.robot_pose)
            self.total_distance_moved += distance
            self.get_logger().debug(f'이동 거리: {distance:.3f}m, 총 거리: {self.total_distance_moved:.3f}m')
    
    def cmd_vel_callback(self, msg: Twist):
        """속도 명령 콜백 (로봇 이동 상태 확인)"""
        linear_speed = abs(msg.linear.x) + abs(msg.linear.y)
        angular_speed = abs(msg.angular.z)
        
        self.is_moving = (linear_speed > 0.01 or angular_speed > 0.01)
        
        if self.is_moving and not self.is_navigating:
            self.get_logger().debug('로봇이 수동으로 이동 중')
    
    def nav_goal_callback(self, msg: PoseStamped):
        """네비게이션 목표 콜백"""
        self.is_navigating = True
        self.get_logger().info(f'네비게이션 목표 설정: ({msg.pose.position.x:.2f}, {msg.pose.position.y:.2f})')
        self.publish_status_message("네비게이션 시작됨")
    
    def calculate_distance(self, pose1: PoseStamped, pose2: PoseStamped) -> float:
        """두 위치 간의 거리 계산"""
        dx = pose2.pose.position.x - pose1.pose.position.x
        dy = pose2.pose.position.y - pose1.pose.position.y
        return np.sqrt(dx*dx + dy*dy)
    
    def calculate_explored_area_ratio(self) -> float:
        """탐험된 영역 비율 계산"""
        if self.current_map is None:
            return 0.0
        
        # 알 수 없는 영역(-1)과 자유 공간(0)의 비율 계산
        data = np.array(self.current_map.data)
        total_cells = len(data)
        unknown_cells = np.sum(data == -1)
        free_cells = np.sum(data == 0)
        
        explored_cells = total_cells - unknown_cells
        explored_ratio = explored_cells / total_cells if total_cells > 0 else 0.0
        
        return explored_ratio
    
    def check_map_update(self):
        """맵 업데이트 조건 확인"""
        current_time = time.time()
        
        # 자동 업데이트가 비활성화된 경우
        if not self.auto_update_enabled:
            return
        
        # 최소 업데이트 간격 확인
        if current_time - self.last_update_time < self.update_interval:
            return
        
        # 로봇 위치가 없는 경우
        if self.robot_pose is None:
            return
        
        # 네비게이션 중 업데이트가 비활성화된 경우
        if self.is_navigating and not self.update_during_navigation:
            return
        
        # 업데이트 조건 확인
        should_update = False
        update_reason = ""
        
        # 1. 충분한 거리 이동
        if self.total_distance_moved >= self.min_movement_distance:
            should_update = True
            update_reason = f"이동 거리 충족 ({self.total_distance_moved:.2f}m)"
        
        # 2. 새로운 영역 탐험
        current_explored_ratio = self.calculate_explored_area_ratio()
        if current_explored_ratio - self.explored_area_ratio >= self.exploration_threshold:
            should_update = True
            update_reason = f"새로운 영역 탐험 ({current_explored_ratio:.3f})"
        
        # 3. 맵 신뢰도 확인
        if self.current_map is not None:
            map_confidence = self.calculate_map_confidence()
            if map_confidence < self.map_confidence_threshold:
                should_update = True
                update_reason = f"맵 신뢰도 낮음 ({map_confidence:.3f})"
        
        # 업데이트 수행
        if should_update:
            self.perform_map_update(update_reason)
    
    def calculate_map_confidence(self) -> float:
        """맵 신뢰도 계산"""
        if self.current_map is None:
            return 0.0
        
        data = np.array(self.current_map.data)
        total_cells = len(data)
        unknown_cells = np.sum(data == -1)
        
        # 알 수 없는 영역이 적을수록 신뢰도가 높음
        confidence = 1.0 - (unknown_cells / total_cells) if total_cells > 0 else 0.0
        return confidence
    
    def perform_map_update(self, reason: str):
        """맵 업데이트 수행"""
        try:
            self.get_logger().info(f'맵 업데이트 요청: {reason}')
            
            # 맵 업데이트 요청 발행
            update_request = Bool()
            update_request.data = True
            self.map_update_request_pub.publish(update_request)
            
            # 상태 업데이트
            self.update_count += 1
            self.last_update_time = time.time()
            self.total_distance_moved = 0.0  # 거리 리셋
            self.explored_area_ratio = self.calculate_explored_area_ratio()
            
            # 상태 메시지 발행
            status_msg = f"맵 업데이트 #{self.update_count}: {reason}"
            self.publish_status_message(status_msg)
            
            self.get_logger().info(f'맵 업데이트 요청 완료: {status_msg}')
            
        except Exception as e:
            self.get_logger().error(f'맵 업데이트 요청 실패: {e}')
            self.publish_status_message(f"맵 업데이트 실패: {e}")
    
    def publish_status(self):
        """주기적 상태 발행"""
        if self.robot_pose is None:
            return
        
        # 탐험 상태 발행
        explored_ratio = self.calculate_explored_area_ratio()
        map_confidence = self.calculate_map_confidence()
        
        exploration_status = (
            f"탐험률: {explored_ratio:.1%}, "
            f"신뢰도: {map_confidence:.1%}, "
            f"이동거리: {self.total_distance_moved:.1f}m, "
            f"업데이트: {self.update_count}회"
        )
        
        exploration_msg = String()
        exploration_msg.data = exploration_status
        self.exploration_status_pub.publish(exploration_msg)
    
    def publish_status_message(self, message: str):
        """상태 메시지 발행"""
        status_msg = String()
        status_msg.data = message
        self.update_status_pub.publish(status_msg)
        self.get_logger().info(message)
    
    def get_statistics(self) -> dict:
        """통계 정보 반환"""
        return {
            'update_count': self.update_count,
            'total_distance_moved': self.total_distance_moved,
            'explored_area_ratio': self.calculate_explored_area_ratio(),
            'map_confidence': self.calculate_map_confidence(),
            'is_navigating': self.is_navigating,
            'is_moving': self.is_moving,
            'last_update_time': self.last_update_time
        }


def main(args=None):
    rclpy.init(args=args)
    node = None
    
    try:
        node = NavigationMapUpdater()
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
