#!/usr/bin/env python3
from RPLCD.i2c import CharLCD

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, UInt8
from geometry_msgs.msg import PoseStamped
import time

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
        
        # 위치 정보 토픽 구독
        self.goal_pose_sub = self.create_subscription(PoseStamped, '/goal_pose', self.goal_pose_callback, 10)
        self.goal_name_sub = self.create_subscription(String, '/goal_location_name', self.goal_name_callback, 10)
        self.location_status_sub = self.create_subscription(String, '/location_status', self.location_status_callback, 10)
        self.rfid_status_sub = self.create_subscription(String, '/rfid_status', self.rfid_status_callback, 10)
        
        # 상태 변수
        self.current_goal = None
        self.current_goal_name = None
        self.current_location_status = "대기 중..."
        self.current_rfid_status = "대기 중..."
        self.last_update_time = time.time()
        
        # 주기적 업데이트 타이머
        self.update_timer = self.create_timer(1.0, self.update_display)  # 1초마다 업데이트
        
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
    
    def goal_pose_callback(self, msg):
        """네비게이션 목표 위치 콜백"""
        self.current_goal = msg
        self.last_update_time = time.time()
        self.get_logger().info(f"New goal: ({msg.pose.position.x:.2f}, {msg.pose.position.y:.2f})")
    
    def goal_name_callback(self, msg):
        """목표 위치 이름 콜백"""
        self.current_goal_name = msg.data
        self.last_update_time = time.time()
        self.get_logger().info(f"Goal location name: {msg.data}")
    
    def location_status_callback(self, msg):
        """위치 관리 상태 콜백"""
        self.current_location_status = msg.data
        self.last_update_time = time.time()
        self.get_logger().debug(f"Location status: {msg.data}")
    
    def rfid_status_callback(self, msg):
        """RFID 상태 콜백"""
        self.current_rfid_status = msg.data
        self.last_update_time = time.time()
        self.get_logger().debug(f"RFID status: {msg.data}")
    
    def update_display(self):
        """LCD 화면 주기적 업데이트"""
        try:
            # 현재 시간
            current_time = time.time()
            
            # 5초 이상 업데이트가 없으면 기본 화면 표시
            if current_time - self.last_update_time > 5.0:
                self.show_default_display()
                return
            
            # 목표 위치가 있으면 네비게이션 정보 표시
            if self.current_goal:
                self.show_navigation_display()
            else:
                # 상태 정보 표시
                self.show_status_display()
                
        except Exception as e:
            self.get_logger().error(f"Display update error: {e}")
    
    def show_default_display(self):
        """기본 화면 표시"""
        try:
            self.lcd.clear()
            self.lcd.cursor_pos = (0, 0)
            self.lcd.write_string("TurtleBot3 Ready")
            self.lcd.cursor_pos = (1, 0)
            self.lcd.write_string("Waiting...")
        except Exception as e:
            self.get_logger().error(f"Default display error: {e}")
    
    def show_navigation_display(self):
        """네비게이션 정보 표시"""
        try:
            self.lcd.clear()
            self.lcd.cursor_pos = (0, 0)
            self.lcd.write_string("Navigating to:")
            
            # 목표 위치 이름 표시 (우선순위)
            if self.current_goal_name:
                # 위치 이름이 16자를 초과하면 줄임
                location_name = self.current_goal_name[:16]
                self.lcd.cursor_pos = (1, 0)
                self.lcd.write_string(location_name)
            elif self.current_goal:
                # 좌표 표시 (백업)
                x = self.current_goal.pose.position.x
                y = self.current_goal.pose.position.y
                coord_text = f"({x:.1f}, {y:.1f})"
                self.lcd.cursor_pos = (1, 0)
                self.lcd.write_string(coord_text)
            
        except Exception as e:
            self.get_logger().error(f"Navigation display error: {e}")
    
    def show_status_display(self):
        """상태 정보 표시"""
        try:
            self.lcd.clear()
            
            # 첫 번째 줄: 위치 관리 상태
            self.lcd.cursor_pos = (0, 0)
            status_line1 = self.current_location_status[:16]  # 16자 제한
            self.lcd.write_string(status_line1)
            
            # 두 번째 줄: RFID 상태
            self.lcd.cursor_pos = (1, 0)
            status_line2 = self.current_rfid_status[:16]  # 16자 제한
            self.lcd.write_string(status_line2)
            
        except Exception as e:
            self.get_logger().error(f"Status display error: {e}")
    
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
