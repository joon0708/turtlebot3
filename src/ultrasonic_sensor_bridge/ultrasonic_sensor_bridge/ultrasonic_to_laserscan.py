#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range, LaserScan
from std_msgs.msg import Header
import math
import numpy as np

class UltrasonicToLaserScan(Node):
    def __init__(self):
        super().__init__('ultrasonic_to_laserscan')
        
        # 초음파 센서 구독
        self.left_sub = self.create_subscription(
            Range, '/ultrasonic/left', self.left_callback, 10)
        self.front_sub = self.create_subscription(
            Range, '/ultrasonic/front', self.front_callback, 10)
        self.right_sub = self.create_subscription(
            Range, '/ultrasonic/right', self.right_callback, 10)
        
        # LaserScan 발행
        self.laserscan_pub = self.create_publisher(LaserScan, '/ultrasonic_scan', 10)
        
        # 센서 값 저장
        self.left_range = 4.0  # 기본값 (최대 거리)
        self.front_range = 4.0
        self.right_range = 4.0
        
        # LaserScan 파라미터 - 전면 집중 범위
        self.angle_min = -math.pi / 2.0  # -90도 (좌측)
        self.angle_max = math.pi / 2.0   # +90도 (우측)
        self.angle_increment = math.pi / 180.0  # 1도씩
        self.range_min = 0.02  # 2cm
        self.range_max = 4.0   # 4m
        
        # 센서 각도 (라디안) - 전면에 집중된 배치
        self.left_angle = math.pi / 4.0    # 45도 (좌측 전방)
        self.front_angle = 0.0             # 0도 (정면)
        self.right_angle = -math.pi / 4.0  # -45도 (우측 전방)
        
        # 센서 각도 범위 (각 센서당 ±15도) - 더 좁은 범위
        self.sensor_angle_range = math.pi / 12.0  # 15도
        
        # 타이머로 LaserScan 발행
        self.timer = self.create_timer(0.1, self.publish_laserscan)
        
        self.get_logger().info('Ultrasonic to LaserScan converter started')
    
    def left_callback(self, msg):
        """좌측 센서 콜백"""
        self.left_range = msg.range
        if math.isnan(self.left_range) or self.left_range <= 0:
            self.left_range = float('inf')  # 무효한 값으로 설정
    
    def front_callback(self, msg):
        """전방 센서 콜백"""
        self.front_range = msg.range
        if math.isnan(self.front_range) or self.front_range <= 0:
            self.front_range = float('inf')  # 무효한 값으로 설정
    
    def right_callback(self, msg):
        """우측 센서 콜백"""
        self.right_range = msg.range
        if math.isnan(self.right_range) or self.right_range <= 0:
            self.right_range = float('inf')  # 무효한 값으로 설정
    
    def publish_laserscan(self):
        """LaserScan 메시지 생성 및 발행"""
        # LaserScan 메시지 생성
        scan_msg = LaserScan()
        scan_msg.header.stamp = self.get_clock().now().to_msg()
        scan_msg.header.frame_id = 'base_link'
        
        scan_msg.angle_min = self.angle_min
        scan_msg.angle_max = self.angle_max
        scan_msg.angle_increment = self.angle_increment
        scan_msg.time_increment = 0.0
        scan_msg.scan_time = 0.1
        scan_msg.range_min = self.range_min
        scan_msg.range_max = self.range_max
        
        # 각도별 거리 배열 생성
        num_angles = int((self.angle_max - self.angle_min) / self.angle_increment) + 1
        ranges = [self.range_max] * num_angles
        
        # 각 센서의 영향 범위에 거리 값 설정
        self.set_sensor_range(ranges, self.left_angle, self.left_range)
        self.set_sensor_range(ranges, self.front_angle, self.front_range)
        self.set_sensor_range(ranges, self.right_angle, self.right_range)
        
        scan_msg.ranges = ranges
        self.laserscan_pub.publish(scan_msg)
    
    def set_sensor_range(self, ranges, sensor_angle, sensor_range):
        """특정 각도 범위에 센서 거리 값 설정"""
        # 무효한 값(inf)인 경우 처리하지 않음
        if math.isinf(sensor_range):
            return
            
        # 센서 각도를 배열 인덱스로 변환
        sensor_index = int((sensor_angle - self.angle_min) / self.angle_increment)
        
        # 센서 영향 범위 계산 (±15도)
        range_indices = int(self.sensor_angle_range / self.angle_increment)
        start_index = max(0, sensor_index - range_indices)
        end_index = min(len(ranges) - 1, sensor_index + range_indices)
        
        # 영향 범위 내의 모든 각도에 거리 값 설정
        for i in range(start_index, end_index + 1):
            # 각도별로 거리 조정 (센서 중심에서 멀어질수록 거리 증가)
            angle_diff = abs(i - sensor_index) * self.angle_increment
            
            # 초음파 센서 특성: 각도가 벌어질수록 감지 거리 감소
            if angle_diff < math.pi / 12.0:  # 15도 이내
                adjusted_range = sensor_range
            else:
                # 각도가 벌어질수록 거리 감소 (초음파 센서 특성)
                adjusted_range = sensor_range * math.cos(angle_diff)
            
            # 유효한 거리인 경우에만 설정
            if self.range_min <= adjusted_range <= self.range_max:
                ranges[i] = min(ranges[i], adjusted_range)  # 더 가까운 거리 선택

def main(args=None):
    rclpy.init(args=args)
    node = UltrasonicToLaserScan()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
