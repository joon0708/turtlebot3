#!/usr/bin/env python3
from RPLCD.i2c import CharLCD

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, UInt8

class LCDController(Node):
    def __init__(self, lcd):
        super().__init__('lcd_controller')
        
        # LCD 객체 저장
        self.lcd = lcd
        
        # 기본 토픽 구독
        self.display_sub = self.create_subscription(String, '/lcd/display', self.display_callback, 10)
        self.clear_sub = self.create_subscription(String, '/lcd/clear', self.clear_callback, 10)
        self.backlight_sub = self.create_subscription(Bool, '/lcd/backlight', self.backlight_callback, 10)
        
        # 고급 토픽 구독
        self.set_cursor_sub = self.create_subscription(String, '/lcd/set_cursor', self.set_cursor_callback, 10)
        self.write_sub = self.create_subscription(String, '/lcd/write', self.write_callback, 10)
        self.clear_line_sub = self.create_subscription(UInt8, '/lcd/clear_line', self.clear_line_callback, 10)
        self.cursor_mode_sub = self.create_subscription(String, '/lcd/cursor_mode', self.cursor_mode_callback, 10)
        
        self.get_logger().info('LCD Controller started')
        
    def display_callback(self, msg):
        """전체 화면 텍스트 표시 토픽"""
        try:
            self.lcd.clear()
            self.lcd.write_string(msg.data)
            self.get_logger().info(f"Display: {msg.data}")
        except Exception as e:
            self.get_logger().error(f"Display error: {e}")
    
    def clear_callback(self, msg):
        """전체 화면 지우기 토픽"""
        try:
            self.lcd.clear()
            self.get_logger().info("LCD cleared")
        except Exception as e:
            self.get_logger().error(f"Clear error: {e}")
    
    def backlight_callback(self, msg):
        """백라이트 제어 토픽"""
        try:
            self.lcd.backlight_enabled = msg.data
            self.get_logger().info(f"Backlight: {'ON' if msg.data else 'OFF'}")
        except Exception as e:
            self.get_logger().error(f"Backlight error: {e}")
    
    def set_cursor_callback(self, msg):
        """커서 위치 설정 토픽 (형식: "row,col")"""
        try:
            # "row,col" 형식 파싱
            parts = msg.data.split(',')
            if len(parts) != 2:
                self.get_logger().error("Invalid format. Use 'row,col'")
                return
            
            row = int(parts[0])
            col = int(parts[1])
            self.lcd.cursor_pos = (row, col)
            self.get_logger().info(f"Cursor set to ({row},{col})")
        except Exception as e:
            self.get_logger().error(f"Set cursor error: {e}")
    
    def write_callback(self, msg):
        """현재 커서 위치에 텍스트 쓰기 토픽"""
        try:
            self.lcd.write_string(msg.data)
            self.get_logger().info(f"Write: {msg.data}")
        except Exception as e:
            self.get_logger().error(f"Write error: {e}")
    
    def clear_line_callback(self, msg):
        """특정 줄 지우기 토픽"""
        try:
            row = msg.data
            self.lcd.cursor_pos = (row, 0)
            self.lcd.write_string(' ' * 16)  # 16자 공백으로 덮어쓰기
            self.get_logger().info(f"Line {row} cleared")
        except Exception as e:
            self.get_logger().error(f"Clear line error: {e}")
            response.data = f"Error: {e}"
        return response
    
    def cursor_mode_callback(self, msg):
        """커서 모드 설정 토픽 (hide/visible/blink)"""
        try:
            mode = msg.data
            if mode in ['hide', 'visible', 'blink']:
                self.lcd.cursor_mode = mode
                self.get_logger().info(f"Cursor mode: {mode}")
            else:
                self.get_logger().error("Invalid mode. Use 'hide', 'visible', or 'blink'")
        except Exception as e:
            self.get_logger().error(f"Cursor mode error: {e}")
    
    def destroy_node(self):
        """노드 종료 시 정리"""
        try:
            self.lcd.clear()
            self.lcd.close()
            self.get_logger().info("LCD hardware cleaned up")
        except Exception as e:
            self.get_logger().error(f"LCD cleanup error: {e}")
        
        self.get_logger().info("LCD Controller shutting down")
        super().destroy_node()

def main(args=None):
    # LCD 초기화
    try:
        lcd = CharLCD('PCF8574', 0x27)
        lcd.clear()
        lcd.write_string("LCD Ready")
        print("LCD initialized successfully")
    except Exception as e:
        print(f"Failed to initialize LCD: {e}")
        return
    
    rclpy.init(args=args)
    
    # 노드 생성
    lcd_controller = LCDController(lcd)
    
    try:
        rclpy.spin(lcd_controller)
    except KeyboardInterrupt:
        pass
    finally:
        lcd_controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
