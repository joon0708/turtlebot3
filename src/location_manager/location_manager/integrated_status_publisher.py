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
        
        # 타이머로 주기적으로 통합 상태 발행
        self.timer = self.create_timer(0.5, self.publish_integrated_status)  # 2Hz
        
        self.get_logger().info('Integrated Status Publisher initialized')
        self.get_logger().info('Publishing to /integrated_status topic')
    
    def location_status_callback(self, msg):
        """위치 관리 상태 업데이트"""
        self.location_status = msg.data
        self.get_logger().debug(f'Location status updated: {self.location_status}')
    
    def rfid_status_callback(self, msg):
        """RFID 상태 업데이트"""
        self.rfid_status = msg.data
        self.get_logger().debug(f'RFID status updated: {self.rfid_status}')
    
    def publish_integrated_status(self):
        """통합 상태 발행"""
        # JSON 형태로 통합 상태 생성
        integrated_data = {
            'timestamp': datetime.now().isoformat(),
            'location_manager': {
                'status': self.location_status,
                'active': True
            },
            'rfid_system': {
                'status': self.rfid_status,
                'active': True
            }
        }
        
        # JSON을 문자열로 변환
        status_msg = String()
        status_msg.data = json.dumps(integrated_data, ensure_ascii=False, indent=2)
        
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
