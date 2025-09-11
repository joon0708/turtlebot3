#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range, LaserScan
from std_msgs.msg import Header
import math
import numpy as np
import time

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
        self.left_range = 0.50  # 기본값 (50cm)
        self.front_range = 0.50
        self.right_range = 0.50
        
        # 장애물 지속 시간 (초) - 회전 중 장애물 놓치지 않도록 더 길게
        self.obstacle_persistence = 6.0  # 6초간 장애물 기억
        
        # 장애물 감지 시간 기록
        self.left_obstacle_time = 0.0
        self.front_obstacle_time = 0.0
        self.right_obstacle_time = 0.0
        
        # LaserScan 파라미터 - 전면 집중 범위
        self.angle_min = -math.pi / 2.0  # -90도 (좌측)
        self.angle_max = math.pi / 2.0   # +90도 (우측)
        self.angle_increment = math.pi / 180.0  # 1도씩
        self.range_min = 0.02  # 2cm
        self.range_max = 0.50  # 50cm
        
        # 센서 각도 (라디안) - 실제 하드웨어에 맞춤
        self.left_angle = math.pi / 6.0    # 30도 (좌측 전방)
        self.front_angle = 0.0             # 0도 (정면)
        self.right_angle = -math.pi / 6.0  # -30도 (우측 전방)
        
        # 센서 각도 범위 (각 센서당 ±15도) - 실제 센서 범위에 맞춤
        self.sensor_angle_range = math.pi / 12.0  # 15도
        
        # 타이머로 LaserScan 발행 (센서 주파수에 맞춤)
        self.timer = self.create_timer(0.025, self.publish_laserscan)  # 40Hz (센서 주파수와 비슷)
        

        
    def left_callback(self, msg):
        """좌측 센서 콜백"""
        old_range = self.left_range
        self.left_range = msg.range
        
        current_time = time.time()
        
        # 장애물 감지 시 시간 기록
        if not math.isnan(self.left_range) and self.left_range > 0 and self.left_range <= 0.50:
            self.left_obstacle_time = current_time
        elif math.isnan(self.left_range) or self.left_range <= 0:
            self.left_range = float('inf')  # 무효한 값으로 설정
        
        # 값이 바뀌면 즉시 LaserScan 발행
        if old_range != self.left_range:
            self.publish_laserscan()
    
    def front_callback(self, msg):
        """전방 센서 콜백"""
        old_range = self.front_range
        self.front_range = msg.range
        
        current_time = time.time()
        
        # 장애물 감지 시 시간 기록
        if not math.isnan(self.front_range) and self.front_range > 0 and self.front_range <= 0.50:
            self.front_obstacle_time = current_time
        elif math.isnan(self.front_range) or self.front_range <= 0:
            self.front_range = float('inf')  # 무효한 값으로 설정
        
        # 값이 바뀌면 즉시 LaserScan 발행
        if old_range != self.front_range:
            self.publish_laserscan()
    
    def right_callback(self, msg):
        """우측 센서 콜백"""
        old_range = self.right_range
        self.right_range = msg.range
        
        current_time = time.time()
        
        # 장애물 감지 시 시간 기록
        if not math.isnan(self.right_range) and self.right_range > 0 and self.right_range <= 0.50:
            self.right_obstacle_time = current_time
        elif math.isnan(self.right_range) or self.right_range <= 0:
            self.right_range = float('inf')  # 무효한 값으로 설정
        
        # 값이 바뀌면 즉시 LaserScan 발행
        if old_range != self.right_range:
            self.publish_laserscan()
    
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
        
        # 각 센서의 영향 범위에 거리 값 설정 (장애물 지속 시간 고려)
        current_time = time.time()
        
        # 좌측 센서: 장애물 지속 시간 내이면 유지
        left_range = self.get_persistent_range(self.left_range, self.left_obstacle_time, current_time)
        self.set_sensor_range(ranges, self.left_angle, left_range)
        
        # 전방 센서: 장애물 지속 시간 내이면 유지
        front_range = self.get_persistent_range(self.front_range, self.front_obstacle_time, current_time)
        self.set_sensor_range(ranges, self.front_angle, front_range)
        
        # 우측 센서: 장애물 지속 시간 내이면 유지
        right_range = self.get_persistent_range(self.right_range, self.right_obstacle_time, current_time)
        self.set_sensor_range(ranges, self.right_angle, right_range)
        
        scan_msg.ranges = ranges
        self.laserscan_pub.publish(scan_msg)
    
    def get_persistent_range(self, current_range, obstacle_time, current_time):
        """장애물 지속 시간을 고려한 거리 값 반환"""
        # 현재 유효한 거리 값이면 그대로 반환
        if not math.isnan(current_range) and current_range > 0 and current_range <= 0.50:
            return current_range
        
        # 무효한 값이지만 장애물 지속 시간 내이면 마지막 유효한 값 유지
        if obstacle_time > 0 and (current_time - obstacle_time) <= self.obstacle_persistence:
            return 0.15  # 15cm로 설정 (더 안전한 거리)
        
        # 장애물 지속 시간 초과 또는 장애물 없음
        return float('inf')
    
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
