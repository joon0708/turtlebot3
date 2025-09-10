#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import time

class UltrasonicSafetyController(Node):
    def __init__(self):
        super().__init__('ultrasonic_safety_controller')
        
        # 초음파 센서 구독
        self.left_sub = self.create_subscription(
            Range, '/ultrasonic/left', self.left_callback, 10)
        self.front_sub = self.create_subscription(
            Range, '/ultrasonic/front', self.front_callback, 10)
        self.right_sub = self.create_subscription(
            Range, '/ultrasonic/right', self.right_callback, 10)
        
        # 원본 cmd_vel 구독 (네비게이션에서 오는 명령)
        self.cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        
        # 안전한 cmd_vel 발행 (우선순위가 높은 토픽)
        self.safe_cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel_safe', 10)
        
        # 상태 발행
        self.status_pub = self.create_publisher(String, '/safety_status', 10)
        
        # 센서 값 저장
        self.left_range = 0.30  # 기본값 (30cm)
        self.front_range = 0.30
        self.right_range = 0.30
        
        # 안전 설정
        self.safety_distance = 0.15  # 15cm 이하에서 정지
        self.stop_duration = 1.0     # 1초간 정지
        self.slow_distance = 0.25    # 25cm 이하에서 감속
        
        # 상태 변수
        self.is_stopped = False
        self.stop_start_time = 0.0
        self.last_cmd_vel = Twist()
        self.safety_status = "NORMAL"
        
        # 타이머로 안전 제어 실행
        self.timer = self.create_timer(0.1, self.safety_control)  # 10Hz
        
        self.get_logger().info('Ultrasonic Safety Controller started')
        self.get_logger().info(f'Safety distance: {self.safety_distance}m, Stop duration: {self.stop_duration}s')
    
    def left_callback(self, msg):
        """좌측 센서 콜백"""
        self.left_range = msg.range
        if self.left_range <= 0 or self.left_range > 0.30:
            self.left_range = 0.30  # 무효한 값 처리
    
    def front_callback(self, msg):
        """전방 센서 콜백"""
        self.front_range = msg.range
        if self.front_range <= 0 or self.front_range > 0.30:
            self.front_range = 0.30  # 무효한 값 처리
    
    def right_callback(self, msg):
        """우측 센서 콜백"""
        self.right_range = msg.range
        if self.right_range <= 0 or self.right_range > 0.30:
            self.right_range = 0.30  # 무효한 값 처리
    
    def cmd_vel_callback(self, msg):
        """원본 cmd_vel 콜백"""
        self.last_cmd_vel = msg
    
    def safety_control(self):
        """안전 제어 로직"""
        current_time = time.time()
        
        # 가장 가까운 거리 확인
        min_distance = min(self.left_range, self.front_range, self.right_range)
        
        # 안전 거리 이하 감지
        if min_distance <= self.safety_distance:
            if not self.is_stopped:
                self.is_stopped = True
                self.stop_start_time = current_time
                self.safety_status = "STOPPED"
                self.get_logger().warn(f'Obstacle detected at {min_distance:.3f}m - STOPPING')
            
            # 정지 시간이 지나면 다시 움직임 허용
            elif current_time - self.stop_start_time >= self.stop_duration:
                self.is_stopped = False
                self.safety_status = "RESUMING"
                self.get_logger().info('Stop duration completed - RESUMING')
        
        # 감속 구간
        elif min_distance <= self.slow_distance:
            self.safety_status = "SLOWING"
            # 속도를 절반으로 감소
            safe_cmd = Twist()
            safe_cmd.linear.x = self.last_cmd_vel.linear.x * 0.5
            safe_cmd.angular.z = self.last_cmd_vel.angular.z * 0.5
            self.safe_cmd_vel_pub.publish(safe_cmd)
        
        # 정상 구간
        else:
            if self.is_stopped:
                self.is_stopped = False
                self.safety_status = "NORMAL"
                self.get_logger().info('Clear path - NORMAL operation')
            
            # 원본 명령 그대로 전달
            self.safe_cmd_vel_pub.publish(self.last_cmd_vel)
        
        # 정지 상태일 때는 정지 명령 발행
        if self.is_stopped:
            stop_cmd = Twist()
            self.safe_cmd_vel_pub.publish(stop_cmd)
        
        # 상태 발행
        status_msg = String()
        status_msg.data = f"{self.safety_status}: L={self.left_range:.2f}, F={self.front_range:.2f}, R={self.right_range:.2f}"
        self.status_pub.publish(status_msg)

def main(args=None):
    rclpy.init(args=args)
    
    controller = UltrasonicSafetyController()
    
    try:
        rclpy.spin(controller)
    except KeyboardInterrupt:
        pass
    finally:
        controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
