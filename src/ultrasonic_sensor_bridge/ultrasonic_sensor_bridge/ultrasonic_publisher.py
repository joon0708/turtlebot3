#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from std_msgs.msg import Header
import time

# DYNAMIXEL SDK import
import sys
sys.path.append('/root/turtlebot3_ws/install/dynamixel_sdk/local/lib/python3.10/dist-packages')

try:
    import dynamixel_sdk as dxl
    DYNAMIXEL_AVAILABLE = True
    print("DYNAMIXEL SDK imported successfully")
except ImportError as e:
    DYNAMIXEL_AVAILABLE = False
    print(f"Warning: DYNAMIXEL SDK not available: {e}")


class UltrasonicPublisher(Node):
    def __init__(self):
        super().__init__('ultrasonic_publisher')
        
        # DYNAMIXEL SDK 설정
        self.port_handler = None
        self.packet_handler = None
        
        # OpenCR 설정
        self.OPENCR_ID = 200  # OpenCR의 ID
        self.DEVICE_NAME = '/dev/ttyACM0'  # OpenCR USB 포트
        self.BAUDRATE = 115200
        
        # 초음파 센서 제어 테이블 주소
        self.ADDR_ULTRASONIC_LEFT = 190
        self.ADDR_ULTRASONIC_FRONT = 194
        self.ADDR_ULTRASONIC_RIGHT = 198
        
        # 이전 값 저장 (nan 필터링용)
        self.prev_left = 0.0
        self.prev_front = 0.0
        self.prev_right = 0.0
        
        # 초음파 센서 토픽 발행
        self.left_pub = self.create_publisher(Range, '/ultrasonic/left', 10)
        self.front_pub = self.create_publisher(Range, '/ultrasonic/front', 10)
        self.right_pub = self.create_publisher(Range, '/ultrasonic/right', 10)
        
        # turtlebot3_ros에서 센서 데이터 구독
        self.sensor_state_sub = self.create_subscription(
            'turtlebot3_msgs/msg/SensorState', 
            '/sensor_state', 
            self.sensor_state_callback, 
            10
        )
        
        # OpenCR 연결 (실제로는 연결하지 않음)
        self.connect_opencr()
        
        self.get_logger().info('Ultrasonic Publisher started')
    
    def connect_opencr(self):
        """OpenCR 연결을 시도하지 않고 turtlebot3_ros에서 센서 데이터를 구독"""
        self.get_logger().info('Using sensor data from turtlebot3_ros instead of direct OpenCR connection')
        self.port_handler = None
    
    def sensor_state_callback(self, msg):
        """turtlebot3_ros에서 센서 데이터를 받아서 초음파 센서 데이터로 변환"""
        try:
            # turtlebot3_msgs/SensorState에서 초음파 센서 데이터 추출
            # 실제 필드명은 turtlebot3_msgs에 따라 다를 수 있음
            if hasattr(msg, 'ultrasonic'):
                # 초음파 센서 데이터가 있는 경우
                ultrasonic_data = msg.ultrasonic
                if len(ultrasonic_data) >= 3:
                    left_val = ultrasonic_data[0] / 1000.0  # mm를 m로 변환
                    front_val = ultrasonic_data[1] / 1000.0
                    right_val = ultrasonic_data[2] / 1000.0
                    
                    # Range 메시지로 발행
                    self.publish_range_msg(self.left_pub, left_val, 'ultrasonic_left')
                    self.publish_range_msg(self.front_pub, front_val, 'ultrasonic_front')
                    self.publish_range_msg(self.right_pub, right_val, 'ultrasonic_right')
            else:
                # 초음파 센서 데이터가 없는 경우 기본값 사용
                self.publish_range_msg(self.left_pub, 4.0, 'ultrasonic_left')
                self.publish_range_msg(self.front_pub, 4.0, 'ultrasonic_front')
                self.publish_range_msg(self.right_pub, 4.0, 'ultrasonic_right')
                
        except Exception as e:
            self.get_logger().error(f'Error processing sensor state: {e}')
    
    def read_control_table(self, address):
        """OpenCR 제어 테이블에서 데이터 읽기"""
        if self.port_handler is None or not DYNAMIXEL_AVAILABLE:
            return None
        
        try:
            # 단일 주소 읽기
            result = self.packet_handler.read4ByteTxRx(
                self.port_handler, self.OPENCR_ID, address)
            
            # result가 튜플인지 확인
            if isinstance(result, tuple):
                if len(result) >= 2:
                    data, error = result[0], result[1]
                else:
                    self.get_logger().warn(f'Unexpected result format: {result}')
                    return None
            else:
                data, error = result, 0
            
            if error != 0:
                self.get_logger().warn(f'Failed to read address {address}: {error}')
                return None
            
            # 4바이트를 float로 변환
            import struct
            float_value = struct.unpack('f', struct.pack('I', data))[0]
            return float_value
            
        except Exception as e:
            self.get_logger().error(f'Error reading control table: {e}')
            return None
    
    
    def publish_range_msg(self, publisher, range_value, frame_id):
        """Range 메시지 발행"""
        msg = Range()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = frame_id
        msg.radiation_type = 0  # ULTRASOUND
        msg.field_of_view = 0.1  # 10 degrees
        msg.min_range = 0.02  # 2cm
        msg.max_range = 4.0   # 4m
        msg.range = range_value
        
        publisher.publish(msg)
    
    def print_values(self, left_val, front_val, right_val):
        """터미널에 값 출력 (디버깅용)"""
        print(f"\n=== OpenCR Ultrasonic Sensors ===")
        print(f"Left (addr 190):   {left_val:.3f}m")
        print(f"Front (addr 194):  {front_val:.3f}m")
        print(f"Right (addr 198):  {right_val:.3f}m")
        print(f"Time:              {time.strftime('%H:%M:%S')}")
        print("=" * 45)

    
    def destroy_node(self):
        """노드 종료 시 정리"""
        if self.port_handler:
            self.port_handler.closePort()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    publisher = UltrasonicPublisher()
    
    try:
        rclpy.spin(publisher)
    except KeyboardInterrupt:
        pass
    finally:
        publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
