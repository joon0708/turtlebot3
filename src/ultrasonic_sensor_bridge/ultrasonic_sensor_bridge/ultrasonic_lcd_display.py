#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from std_msgs.msg import String
import time


class UltrasonicLCDDisplay(Node):
    def __init__(self):
        super().__init__('ultrasonic_lcd_display')
        
        # 초음파 센서 토픽 구독
        self.left_sub = self.create_subscription(Range, '/ultrasonic/left', self.left_callback, 10)
        self.front_sub = self.create_subscription(Range, '/ultrasonic/front', self.front_callback, 10)
        self.right_sub = self.create_subscription(Range, '/ultrasonic/right', self.right_callback, 10)
        
        # LCD 토픽 발행
        self.lcd_display_pub = self.create_publisher(String, '/lcd/display', 10)
        self.lcd_clear_pub = self.create_publisher(String, '/lcd/clear', 10)
        self.lcd_cursor_pub = self.create_publisher(String, '/lcd/set_cursor', 10)
        self.lcd_write_pub = self.create_publisher(String, '/lcd/write', 10)
        
        # 센서 값 저장
        self.left_distance = 0.0
        self.front_distance = 0.0
        self.right_distance = 0.0
        
        # 타이머 설정 (1초마다 LCD 업데이트)
        self.timer = self.create_timer(1.0, self.update_lcd)
        
        self.get_logger().info('Ultrasonic LCD Display started')
        
        # LCD 초기화
        self.init_lcd()
    
    def init_lcd(self):
        """LCD 초기화"""
        try:
            # LCD 지우기
            clear_msg = String()
            clear_msg.data = ""
            self.lcd_clear_pub.publish(clear_msg)
            
            
            self.get_logger().info('LCD initialized')
        except Exception as e:
            self.get_logger().error(f'LCD init error: {e}')
    
    def left_callback(self, msg):
        """왼쪽 센서 콜백"""
        self.left_distance = msg.range
        self.get_logger().debug(f'Left: {self.left_distance:.3f}m')
    
    def front_callback(self, msg):
        """앞쪽 센서 콜백"""
        self.front_distance = msg.range
        self.get_logger().debug(f'Front: {self.front_distance:.3f}m')
    
    def right_callback(self, msg):
        """오른쪽 센서 콜백"""
        self.right_distance = msg.range
        self.get_logger().debug(f'Right: {self.right_distance:.3f}m')
    
    def update_lcd(self):
        """LCD 업데이트"""
        try:
            # LCD 지우기
            clear_msg = String()
            clear_msg.data = ""
            self.lcd_clear_pub.publish(clear_msg)
            

            time.sleep(0.1)
            
            
            
            # 센서 값 표시

            sensor_msg = String()
            sensor_msg.data = f"L:{self.left_distance:.2f} F:{self.front_distance:.2f}"
            self.lcd_write_pub.publish(sensor_msg)

            time.sleep(0.1)
            # 두 번째 줄: 센서 값들
            # 커서를 두 번째 줄로 이동
            cursor_msg = String()
            cursor_msg.data = "1,0"
            self.lcd_cursor_pub.publish(cursor_msg)
            
            time.sleep(0.1)

            sensor_msg = String()
            sensor_msg.data = f"R:{self.right_distance:.2f}"
            self.lcd_write_pub.publish(sensor_msg)
            
            # 터미널에도 출력
            self.get_logger().info(f'LCD Updated - L:{self.left_distance:.3f}m F:{self.front_distance:.3f}m R:{self.right_distance:.3f}m')
            
        except Exception as e:
            self.get_logger().error(f'LCD update error: {e}')
    
    def display_simple(self):
        """간단한 표시 방식 (한 줄에 모든 정보)"""
        try:
            # LCD 지우기
            clear_msg = String()
            clear_msg.data = ""
            self.lcd_clear_pub.publish(clear_msg)
            
            sensor_msg = String()
            sensor_msg.data = f"L:{self.left_distance:.2f} F:{self.front_distance:.2f}"
            self.lcd_write_pub.publish(sensor_msg)

            time.sleep(0.1)
            # 두 번째 줄: 센서 값들
            # 커서를 두 번째 줄로 이동
            cursor_msg = String()
            cursor_msg.data = "1,0"
            self.lcd_cursor_pub.publish(cursor_msg)
            
            time.sleep(0.1)

            sensor_msg = String()
            sensor_msg.data = f"R:{self.right_distance:.2f}"
            self.lcd_write_pub.publish(sensor_msg)
            
        except Exception as e:
            self.get_logger().error(f'Simple display error: {e}')


def main(args=None):
    rclpy.init(args=args)
    
    display = UltrasonicLCDDisplay()
    
    try:
        rclpy.spin(display)
    except KeyboardInterrupt:
        pass
    finally:
        display.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
