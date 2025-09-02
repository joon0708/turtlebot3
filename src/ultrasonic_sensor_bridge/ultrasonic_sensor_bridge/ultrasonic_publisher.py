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
        
        # 타이머 설정 (100ms마다 읽기)
        self.timer = self.create_timer(0.1, self.read_and_publish_ultrasonic)
        
        # OpenCR 연결
        self.connect_opencr()
        
        self.get_logger().info('Ultrasonic Publisher started')
    
    def connect_opencr(self):
        """OpenCR에 DYNAMIXEL SDK로 연결"""
        if not DYNAMIXEL_AVAILABLE:
            self.get_logger().error('DYNAMIXEL SDK not available')
            return
        
        try:
            # 포트 핸들러 초기화
            self.port_handler = dxl.PortHandler(self.DEVICE_NAME)
            
            # 패킷 핸들러 초기화
            self.packet_handler = dxl.PacketHandler(2.0)  # Protocol 2.0
            
            # 포트 열기
            if self.port_handler.openPort():
                self.get_logger().info(f'Opened port: {self.DEVICE_NAME}')
            else:
                self.get_logger().error(f'Failed to open port: {self.DEVICE_NAME}')
                return
            
            # 보드레이트 설정
            if self.port_handler.setBaudRate(self.BAUDRATE):
                self.get_logger().info(f'Changed baudrate to: {self.BAUDRATE}')
            else:
                self.get_logger().error('Failed to change baudrate')
                return
            
            self.get_logger().info('Successfully connected to OpenCR')
            
        except Exception as e:
            self.get_logger().error(f'Failed to connect to OpenCR: {e}')
            self.port_handler = None
    
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
    
    def read_and_publish_ultrasonic(self):
        """3개 초음파 센서 값 읽기 및 발행"""
        if self.port_handler is None or not DYNAMIXEL_AVAILABLE:
            return
        
        try:
            # 3개 센서 값 읽기
            left_val = self.read_control_table(self.ADDR_ULTRASONIC_LEFT) or 0.0
            front_val = self.read_control_table(self.ADDR_ULTRASONIC_FRONT) or 0.0
            right_val = self.read_control_table(self.ADDR_ULTRASONIC_RIGHT) or 0.0
            
            # nan 값 필터링 (이전 값으로 대체)
            import math
            if math.isnan(left_val) or left_val == 0.0:
                left_val = self.prev_left
            else:
                self.prev_left = left_val
                
            if math.isnan(front_val) or front_val == 0.0:
                front_val = self.prev_front
            else:
                self.prev_front = front_val
                
            if math.isnan(right_val) or right_val == 0.0:
                right_val = self.prev_right
            else:
                self.prev_right = right_val
            
            # Range 메시지 생성 및 발행
            self.publish_range_msg(self.left_pub, left_val, 'ultrasonic_left')
            self.publish_range_msg(self.front_pub, front_val, 'ultrasonic_front')
            self.publish_range_msg(self.right_pub, right_val, 'ultrasonic_right')
            
            # 터미널 출력 (디버깅용, 필요시 주석 해제)
            # self.print_values(left_val, front_val, right_val)
            
        except Exception as e:
            self.get_logger().error(f'Error in ultrasonic read: {e}')
    
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
