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
        
        # 센서 값 저장 (초기값은 None으로 설정)
        self.left_range = None
        self.front_range = None
        self.right_range = None
        
        # 센서 값 리셋을 위한 타이머 (10초마다)
        self.last_reset_time = time.time()
        
        # 히스토리 관련 코드 (나중에 사용할 수 있도록 주석 처리)
        # self.left_history = [None] * 10
        # self.front_history = [None] * 10
        # self.right_history = [None] * 10
        # self.left_index = 0
        # self.front_index = 0
        # self.right_index = 0
        
        # 안전 설정 (파라미터에서 가져오기)
        self.declare_parameter('safety_distance', 0.40)  # 정지 거리 (40cm)
        self.declare_parameter('slow_distance', 0.45)    # 감속 거리 (45cm)
        self.declare_parameter('warning_distance', 0.50) # 경고 거리 (50cm)
        self.declare_parameter('stop_duration', 3.0)
        
        # 히스테리시스 설정 (경계에서 변동 방지)
        self.hysteresis = 0.02  # 2cm 여유
        
        self.safety_distance = self.get_parameter('safety_distance').get_parameter_value().double_value
        self.slow_distance = self.get_parameter('slow_distance').get_parameter_value().double_value
        self.warning_distance = self.get_parameter('warning_distance').get_parameter_value().double_value
        self.stop_duration = self.get_parameter('stop_duration').get_parameter_value().double_value
        
        # 상태 변수
        self.is_stopped = False
        self.stop_start_time = 0.0
        self.last_cmd_vel = Twist()
        self.safety_status = "NORMAL"
        
        # 타이머로 안전 제어 실행
        self.timer = self.create_timer(0.2, self.safety_control)  # 5Hz (더 안정적)
        
        self.get_logger().info('Ultrasonic Safety Controller started')
        self.get_logger().info(f'Safety zones: STOP={self.safety_distance}m, SLOW={self.slow_distance}m, WARNING={self.warning_distance}m')
        self.get_logger().info(f'Stop duration: {self.stop_duration}s')
    
    def left_callback(self, msg):
        """좌측 센서 콜백"""
        # 간단한 방식: 유효한 값이면 바로 사용 (50cm까지)
        if msg.range > 0 and msg.range <= 0.50:
            self.left_range = msg.range
        else:
            # 무효한 값이면 None으로 설정
            self.left_range = None
        
        # 히스토리 방식 (나중에 사용할 수 있도록 주석 처리)
        # self.get_logger().info(f'Left callback: {msg.range}')
        # if msg.range > 0 and msg.range <= 0.50:
        #     self.left_history[self.left_index] = msg.range
        #     self.left_range = msg.range
        # else:
        #     self.left_history[self.left_index] = None
        #     # self.left_range는 이전 값 유지
        # self.left_index = (self.left_index + 1) % 10
    
    def front_callback(self, msg):
        """전방 센서 콜백"""
        # 간단한 방식: 유효한 값이면 바로 사용 (50cm까지)
        if msg.range > 0 and msg.range <= 0.50:
            self.front_range = msg.range
        else:
            # 무효한 값이면 None으로 설정
            self.front_range = None
        
        # 개별 센서 로그는 제거 (너무 많음)
        
        # 히스토리 방식 (나중에 사용할 수 있도록 주석 처리)
        # if msg.range > 0 and msg.range <= 0.50:
        #     self.front_history[self.front_index] = msg.range
        #     self.front_range = msg.range
        # else:
        #     self.front_history[self.front_index] = None
        #     # self.front_range는 이전 값 유지
        # self.front_index = (self.front_index + 1) % 10
    
    def right_callback(self, msg):
        """우측 센서 콜백"""
        # 간단한 방식: 유효한 값이면 바로 사용 (50cm까지)
        if msg.range > 0 and msg.range <= 0.50:
            self.right_range = msg.range
        else:
            # 무효한 값이면 None으로 설정
            self.right_range = None
        
        # 개별 센서 로그는 제거 (너무 많음)
        
        # 히스토리 방식 (나중에 사용할 수 있도록 주석 처리)
        # if msg.range > 0 and msg.range <= 0.50:
        #     self.right_history[self.right_index] = msg.range
        #     self.right_range = msg.range
        # else:
        #     self.right_history[self.right_index] = None
        #     # self.right_range는 이전 값 유지
        # self.right_index = (self.right_index + 1) % 10
    
    def cmd_vel_callback(self, msg):
        """원본 cmd_vel 콜백"""
        self.last_cmd_vel = msg
    
    def safety_control(self):
        """안전 제어 로직"""
        current_time = time.time()
        
        # 10초마다 센서 값 리셋 (이전 값 유지 문제 해결)
        if current_time - self.last_reset_time > 10.0:
            self.left_range = None
            self.front_range = None
            self.right_range = None
            self.last_reset_time = current_time
            self.get_logger().info('Sensor values reset due to timeout')
        
        # 간단한 방식: 현재 센서 값 바로 사용
        valid_sensors = []
        
        # 좌측 센서: 현재 값이 유효하면 사용 (50cm까지)
        if self.left_range is not None and 0 < self.left_range <= 0.50:
            valid_sensors.append(self.left_range)
        
        # 전방 센서: 현재 값이 유효하면 사용 (50cm까지)
        if self.front_range is not None and 0 < self.front_range <= 0.50:
            valid_sensors.append(self.front_range)
        
        # 우측 센서: 현재 값이 유효하면 사용 (50cm까지)
        if self.right_range is not None and 0 < self.right_range <= 0.50:
            valid_sensors.append(self.right_range)
        
        # 히스토리 방식 (나중에 사용할 수 있도록 주석 처리)
        # left_valid = [val for val in self.left_history if val is not None and 0 < val <= 0.50]
        # if left_valid:
        #     valid_sensors.append(left_valid[-1])
        # front_valid = [val for val in self.front_history if val is not None and 0 < val <= 0.50]
        # if front_valid:
        #     valid_sensors.append(front_valid[-1])
        # right_valid = [val for val in self.right_history if val is not None and 0 < val <= 0.50]
        # if right_valid:
        #     valid_sensors.append(right_valid[-1])
        
        # 유효한 센서가 없으면 장애물 없는 것으로 인식 (멀리 있을 때)
        if not valid_sensors:
            self.safety_status = "NORMAL"
            
            # 센서 감지 없음 상태 로그 출력
            left_str = f"{self.left_range:.2f}" if self.left_range is not None else "None"
            front_str = f"{self.front_range:.2f}" if self.front_range is not None else "None"
            right_str = f"{self.right_range:.2f}" if self.right_range is not None else "None"
            self.get_logger().info(f'L:{left_str} F:{front_str} R:{right_str} | Min:None | {self.safety_status}')
            
            # 정지 상태 해제하고 원본 명령 전달
            if self.is_stopped:
                self.is_stopped = False
                self.get_logger().info('No sensors detected - resuming normal operation')
            
            # 원본 명령 그대로 전달 (장애물 없음)
            self.safe_cmd_vel_pub.publish(self.last_cmd_vel)
            return
        
        # 가장 가까운 거리 확인 (유효한 센서만 사용)
        min_distance = min(valid_sensors)
        
        # 거리값과 상태를 한 줄로 표시 (None 값 처리)
        left_str = f"{self.left_range:.2f}" if self.left_range is not None else "None"
        front_str = f"{self.front_range:.2f}" if self.front_range is not None else "None"
        right_str = f"{self.right_range:.2f}" if self.right_range is not None else "None"
        self.get_logger().info(f'L:{left_str} F:{front_str} R:{right_str} | Min:{min_distance:.2f} | {self.safety_status}')
        
        # 안전 거리 이하 감지
        if min_distance <= self.safety_distance:
            if not self.is_stopped:
                self.is_stopped = True
                self.stop_start_time = current_time
                self.safety_status = "STOPPED"
                self.get_logger().warn(f'Obstacle detected at {min_distance:.3f}m - STOPPING')
            
            # 정지 시간이 지나면 다시 움직임 허용 (히스테리시스로 여유 추가)
            elif current_time - self.stop_start_time >= self.stop_duration and min_distance > (self.safety_distance + self.hysteresis):
                self.is_stopped = False
                self.safety_status = "RESUMING"
                self.get_logger().info('Stop duration completed and path clear - RESUMING')
        
        # 2단계: 감속 구간 (히스테리시스 적용)
        elif min_distance <= (self.slow_distance + self.hysteresis):
            self.safety_status = "SLOWING"
            # 속도를 절반으로 감소
            safe_cmd = Twist()
            safe_cmd.linear.x = self.last_cmd_vel.linear.x * 0.5
            safe_cmd.angular.z = self.last_cmd_vel.angular.z * 0.5
            self.safe_cmd_vel_pub.publish(safe_cmd)
            self.get_logger().info(f'Obstacle at {min_distance:.3f}m - SLOWING DOWN')
        
        # 3단계: 경고 구간 (히스테리시스 적용)
        elif min_distance <= (self.warning_distance + self.hysteresis):
            self.safety_status = "WARNING"
            # 속도를 75%로 감소
            safe_cmd = Twist()
            safe_cmd.linear.x = self.last_cmd_vel.linear.x * 0.75
            safe_cmd.angular.z = self.last_cmd_vel.angular.z * 0.75
            self.safe_cmd_vel_pub.publish(safe_cmd)
            self.get_logger().info(f'Obstacle at {min_distance:.3f}m - WARNING (reduced speed)')
        
        # 4단계: 정상 구간 (35cm 초과)
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
        
        # 상태 발행 (None 값 처리)
        left_str = f"{self.left_range:.2f}" if self.left_range is not None else "None"
        front_str = f"{self.front_range:.2f}" if self.front_range is not None else "None"
        right_str = f"{self.right_range:.2f}" if self.right_range is not None else "None"
        status_msg = String()
        status_msg.data = f"{self.safety_status}: L={left_str}, F={front_str}, R={right_str}"
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
