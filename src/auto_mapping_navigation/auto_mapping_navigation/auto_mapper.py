#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import OccupancyGrid, Path
from std_msgs.msg import Bool, String
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
import numpy as np
import math
import random
from enum import Enum

class MappingState(Enum):
    EXPLORING = "exploring"
    NAVIGATING = "navigating"
    IDLE = "idle"

class AutoMapper(Node):
    def __init__(self):
        super().__init__('auto_mapper')
        
        # 상태 관리
        self.state = MappingState.EXPLORING
        self.map_completion_threshold = 80.0  # 맵 완성도 임계값
        
        # 맵 데이터
        self.current_map = None
        self.map_completion_score = 0.0
        
        # 탐색 전략
        self.exploration_waypoints = []
        self.current_waypoint_index = 0
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.mapping_status_pub = self.create_publisher(String, '/mapping_status', 10)
        
        # Subscribers
        self.map_sub = self.create_subscription(OccupancyGrid, '/map', self.map_callback, 10)
        self.nav_goal_sub = self.create_subscription(PoseStamped, '/nav_goal', self.nav_goal_callback, 10)
        
        # Action clients
        self.nav_action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # Timers
        self.mapping_timer = self.create_timer(1.0, self.mapping_loop)
        self.exploration_timer = self.create_timer(0.1, self.exploration_loop)
        
        # 파라미터
        self.declare_parameter('map_completion_threshold', 80.0)
        self.declare_parameter('exploration_speed', 0.2)
        self.declare_parameter('exploration_angular_speed', 0.5)
        
        self.map_completion_threshold = self.get_parameter('map_completion_threshold').value
        self.exploration_speed = self.get_parameter('exploration_speed').value
        self.exploration_angular_speed = self.get_parameter('exploration_angular_speed').value
        
        self.get_logger().info('Auto Mapper initialized')
        
    def map_callback(self, msg):
        """맵 데이터 수신 및 완성도 계산"""
        self.current_map = msg
        self.map_completion_score = self.calculate_map_completion()
        
        # 맵 완성도가 임계값을 넘으면 탐색 중지
        if self.map_completion_score >= self.map_completion_threshold:
            if self.state == MappingState.EXPLORING:
                self.get_logger().info(f'Map completion reached {self.map_completion_score:.1f}% - Stopping exploration')
                self.state = MappingState.IDLE
                self.stop_robot()
                self.mapping_status_pub.publish(String(data=f"Mapping completed: {self.map_completion_score:.1f}%"))
    
    def calculate_map_completion(self):
        """맵 완성도 계산 (0-100%)"""
        if self.current_map is None:
            return 0.0
            
        map_data = np.array(self.current_map.data)
        explored_cells = np.sum(map_data != -1)  # -1은 미탐색 영역
        total_cells = len(map_data)
        
        if total_cells == 0:
            return 0.0
            
        coverage = explored_cells / total_cells * 100.0
        
        # 간단한 품질 메트릭 추가
        quality_bonus = 0.0
        if coverage > 50:
            # 탐색된 영역의 품질 평가
            explored_data = map_data[map_data != -1]
            if len(explored_data) > 0:
                # 장애물과 자유 공간의 균형
                free_space = np.sum(explored_data == 0)
                occupied_space = np.sum(explored_data == 100)
                if free_space + occupied_space > 0:
                    quality_bonus = min(10.0, (free_space / (free_space + occupied_space)) * 10.0)
        
        return min(100.0, coverage + quality_bonus)
    
    def exploration_loop(self):
        """자동 탐색 루프"""
        if self.state != MappingState.EXPLORING:
            return
            
        # 간단한 탐색 전략: 랜덤 움직임
        self.random_exploration()
    
    def random_exploration(self):
        """랜덤 탐색 움직임"""
        twist = Twist()
        
        # 70% 확률로 전진, 30% 확률로 회전
        if random.random() < 0.7:
            twist.linear.x = self.exploration_speed
            twist.angular.z = 0.0
        else:
            twist.linear.x = 0.0
            twist.angular.z = random.choice([-1, 1]) * self.exploration_angular_speed
        
        self.cmd_vel_pub.publish(twist)
    
    def nav_goal_callback(self, msg):
        """네비게이션 목표 수신"""
        if self.state == MappingState.EXPLORING:
            self.get_logger().info('Navigation goal received - switching to navigation mode')
            self.state = MappingState.NAVIGATING
            self.stop_robot()
            
        # 네비게이션 액션 실행
        self.execute_navigation(msg)
    
    def execute_navigation(self, goal_pose):
        """네비게이션 실행"""
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = goal_pose
        
        self.get_logger().info('Executing navigation to goal')
        
        # 네비게이션 액션 전송
        self.nav_action_client.send_goal_async(goal_msg)
    
    def stop_robot(self):
        """로봇 정지"""
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)
    
    def mapping_loop(self):
        """메인 매핑 루프"""
        if self.current_map is None:
            return
            
        # 상태별 로깅
        if self.state == MappingState.EXPLORING:
            self.get_logger().info(f'Exploring... Map completion: {self.map_completion_score:.1f}%')
        elif self.state == MappingState.NAVIGATING:
            self.get_logger().info('Navigation mode active')
        elif self.state == MappingState.IDLE:
            self.get_logger().info('Mapping completed - waiting for navigation commands')

def main(args=None):
    rclpy.init(args=args)
    auto_mapper = AutoMapper()
    
    try:
        rclpy.spin(auto_mapper)
    except KeyboardInterrupt:
        pass
    finally:
        auto_mapper.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

