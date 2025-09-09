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


class UltrasonicPublisherDirect(Node):
    def __init__(self):
        super().__init__('ultrasonic_publisher_direct')
        
        # DYNAMIXEL SDK 설정
        self.port_handler = None
        self.packet_handler = None
        
        # OpenCR 설정
        self.OPENCR_ID = 200  # OpenCR의 ID
        self.DEVICE_NAME = '/dev/ttyACM0'  # OpenCR USB 포트
        self.BAUDRATE = 1000000
        
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
        
        # OpenCR 직접 연결
        self.connect_opencr()
        
        # 타이머로 주기적으로 센서 데이터 읽기
        self.timer = self.create_timer(0.05, self.read_and_publish_sensors)  # 20Hz
        
        self.get_logger().info('Ultrasonic Publisher Direct started with OpenCR connection')
    
    def connect_opencr(self):
        """OpenCR에 직접 연결"""
        if not DYNAMIXEL_AVAILABLE:
            self.get_logger().error("DYNAMIXEL SDK not available")
            return False
        
        try:
            # 포트 핸들러 초기화
            self.port_handler = dxl.PortHandler(self.DEVICE_NAME)
            self.packet_handler = dxl.PacketHandler(2.0)
            
            # 포트 열기
            if not self.port_handler.openPort():
                self.get_logger().error(f"Failed to open port {self.DEVICE_NAME}")
                return False
            
            # 보드레이트 설정
            if not self.port_handler.setBaudRate(self.BAUDRATE):
                self.get_logger().error(f"Failed to set baudrate to {self.BAUDRATE}")
                return False
            
            self.get_logger().info(f"Successfully connected to OpenCR at {self.DEVICE_NAME}")
            return True
            
        except Exception as e:
            self.get_logger().error(f"Error connecting to OpenCR: {e}")
            return False
    
    def read_and_publish_sensors(self):
        """OpenCR에서 직접 초음파 센서 데이터를 읽어서 발행"""
        if self.port_handler is None:
            return
        
        try:
            # 3개 초음파 센서 데이터 읽기
            left_val = self.read_control_table(self.ADDR_ULTRASONIC_LEFT)
            front_val = self.read_control_table(self.ADDR_ULTRASONIC_FRONT)
            right_val = self.read_control_table(self.ADDR_ULTRASONIC_RIGHT)
            
            # nan 값 필터링
            if left_val is None or left_val != left_val:  # nan 체크
                left_val = self.prev_left
            else:
                self.prev_left = left_val
                
            if front_val is None or front_val != front_val:
                front_val = self.prev_front
            else:
                self.prev_front = front_val
                
            if right_val is None or right_val != right_val:
                right_val = self.prev_right
            else:
                self.prev_right = right_val
            
            # 초음파 센서 범위 제한 (너무 멀면 감지 안함)
            MAX_RANGE = 1.0  # 1미터 이상이면 무효
            MIN_RANGE = 0.02  # 2cm 미만이면 무효
            
            if left_val > MAX_RANGE or left_val < MIN_RANGE:
                left_val = 0.0
            if front_val > MAX_RANGE or front_val < MIN_RANGE:
                front_val = 0.0
            if right_val > MAX_RANGE or right_val < MIN_RANGE:
                right_val = 0.0
            
            # Range 메시지로 발행
            self.publish_range_msg(self.left_pub, left_val, 'ultrasonic_left')
            self.publish_range_msg(self.front_pub, front_val, 'ultrasonic_front')
            self.publish_range_msg(self.right_pub, right_val, 'ultrasonic_right')
            
            # 디버깅용 로그
            self.get_logger().info(f'Ultrasonic: L={left_val:.3f}, F={front_val:.3f}, R={right_val:.3f}')
                
        except Exception as e:
            self.get_logger().error(f'Error reading sensors: {e}')
    
    def read_control_table(self, address):
        """OpenCR 제어 테이블에서 데이터 읽기"""
        if self.port_handler is None or not DYNAMIXEL_AVAILABLE:
            return None
        
        try:
            # 단일 주소 읽기 - DYNAMIXEL SDK 반환값 처리
            result = self.packet_handler.read4ByteTxRx(
                self.port_handler, self.OPENCR_ID, address)
            
            # result가 튜플인지 확인하고 적절히 처리
            if isinstance(result, tuple):
                if len(result) >= 2:
                    data, error = result[0], result[1]
                else:
                    self.get_logger().warn(f'Unexpected result format: {result}')
                    return None
            else:
                # 단일 값인 경우 (성공)
                data = result
                error = 0
            
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
    
    def destroy_node(self):
        """노드 종료 시 정리"""
        if self.port_handler:
            self.port_handler.closePort()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    publisher = UltrasonicPublisherDirect()
    
    try:
        rclpy.spin(publisher)
    except KeyboardInterrupt:
        pass
    finally:
        publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
