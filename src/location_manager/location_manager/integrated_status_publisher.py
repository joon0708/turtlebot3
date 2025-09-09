#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
from datetime import datetime

class IntegratedStatusPublisher(Node):
    def __init__(self):
        super().__init__('integrated_status_publisher')
        
        # 통합 상태 퍼블리셔
        self.integrated_status_pub = self.create_publisher(String, '/integrated_status', 10)
        
        # 구독자들
        self.location_status_sub = self.create_subscription(
            String, '/location_status', self.location_status_callback, 10)
        self.rfid_status_sub = self.create_subscription(
            String, '/rfid_status', self.rfid_status_callback, 10)
        
        # 상태 저장
        self.location_status = "시스템 시작 중..."
        self.rfid_status = "RFID 시스템 시작 중..."
        
        # 타이머 비활성화 - 응답식으로만 발행
        # self.timer = self.create_timer(2.0, self.publish_integrated_status)  # 주기적 발행 비활성화
        
        self.get_logger().info('Integrated Status Publisher initialized')
        self.get_logger().info('Publishing to /integrated_status topic')
    
    def location_status_callback(self, msg):
        """위치 관리 상태 업데이트"""
        self.location_status = msg.data
        self.get_logger().debug(f'Location status updated: {self.location_status}')
        # 상태 변경 시 즉시 통합 상태 발행 (응답식)
        self.publish_integrated_status()
    
    def rfid_status_callback(self, msg):
        """RFID 상태 업데이트"""
        self.rfid_status = msg.data
        self.get_logger().debug(f'RFID status updated: {self.rfid_status}')
        # 상태 변경 시 즉시 통합 상태 발행 (응답식)
        self.publish_integrated_status()
    
    def publish_integrated_status(self):
        """통합 상태 발행"""
        # 깔끔한 텍스트 형태로 통합 상태 생성
        status_msg = String()
        status_msg.data = f"=== 통합 시스템 상태 ===\n위치 관리: {self.location_status}\nRFID 시스템: {self.rfid_status}\n시간: {datetime.now().strftime('%H:%M:%S')}"
        
        # 통합 상태 발행
        self.integrated_status_pub.publish(status_msg)

def main(args=None):
    rclpy.init(args=args)
    
    node = IntegratedStatusPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
