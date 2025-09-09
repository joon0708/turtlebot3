#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
import yaml
import os
import json
from datetime import datetime
import time

class RFIDLocationMapper(Node):
    def __init__(self):
        super().__init__('rfid_location_mapper')
        
        # 저장 파일 경로
        self.config_dir = os.path.expanduser('~/.turtlebot3_rfid_mappings')
        self.mappings_file = os.path.join(self.config_dir, 'rfid_location_mappings.yaml')
        
        # RFID 태그와 위치 매핑
        self.rfid_location_mapping = {}
        
        # Publishers
        self.nav_goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.status_pub = self.create_publisher(String, '/rfid_status', 10)
        self.location_cmd_pub = self.create_publisher(String, '/location_command', 10)
        
        # Subscribers
        self.rfid_sub = self.create_subscription(String, '/rfid/tag', self.rfid_callback, 10)
        self.location_cmd_sub = self.create_subscription(String, '/rfid_command', self.rfid_command_callback, 10)
        
        # 초기화
        self.load_mappings()
        
        # 상태 변수
        self.last_rfid_time = 0.0
        self.cooldown_sec = 2.0  # RFID 태그 간 쿨다운 시간
        
        self.get_logger().info('RFID Location Mapper initialized')
        self.get_logger().info('Available commands: list, map <tag_id> <location_name>, unmap <tag_id>, clear')
        self.get_logger().info('RFID tag detection enabled - will navigate to mapped locations')
        
    def load_mappings(self):
        """저장된 RFID 매핑 로드"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            if os.path.exists(self.mappings_file):
                with open(self.mappings_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and 'rfid_mappings' in data:
                        self.rfid_location_mapping = data['rfid_mappings']
                        self.get_logger().info(f'Loaded {len(self.rfid_location_mapping)} RFID mappings')
                    else:
                        self.rfid_location_mapping = {}
            else:
                self.rfid_location_mapping = {}
                self.get_logger().info('No existing RFID mappings file found')
        except Exception as e:
            self.get_logger().error(f'Error loading RFID mappings: {e}')
            self.rfid_location_mapping = {}
    
    def save_mappings(self):
        """RFID 매핑 저장"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            data = {
                'rfid_mappings': self.rfid_location_mapping,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.mappings_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            self.get_logger().info('RFID mappings saved successfully')
        except Exception as e:
            self.get_logger().error(f'Error saving RFID mappings: {e}')
    
    def rfid_callback(self, msg):
        """RFID 태그 감지 시 호출되는 콜백"""
        current_time = time.time()
        
        # 쿨다운 체크
        if current_time - self.last_rfid_time < self.cooldown_sec:
            self.get_logger().debug(f'쿨다운 중: {self.cooldown_sec - (current_time - self.last_rfid_time):.1f}초 남음')
            return
        
        tag_id = msg.data.strip()
        self.get_logger().info(f'RFID 태그 감지: {tag_id}')
        self.last_rfid_time = current_time
        
        # RFID 태그와 위치 매핑 확인
        if tag_id in self.rfid_location_mapping:
            location_name = self.rfid_location_mapping[tag_id]['name']
            self.get_logger().info(f'RFID 태그 {tag_id}에 매핑된 위치: {location_name}')
            # location_manager의 /location_command 토픽으로 이동 명령 전송
            self.send_location_command(f"go {location_name}")
        else:
            self.get_logger().warn(f'RFID 태그 {tag_id}에 매핑된 위치가 없습니다')
            self.publish_status_message(f"RFID {tag_id}: 매핑된 위치 없음")
    
    def go_to_location(self, location_data):
        """저장된 위치로 이동"""
        # PoseStamped 메시지 생성
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        
        pose.pose.position.x = location_data['x']
        pose.pose.position.y = location_data['y']
        pose.pose.position.z = location_data.get('z', 0.0)
        
        # yaw를 quaternion으로 변환
        yaw = location_data['yaw']
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = 0.0  # sin(yaw / 2.0)
        pose.pose.orientation.w = 1.0  # cos(yaw / 2.0)
        
        # 네비게이션 목표 발행
        self.nav_goal_pub.publish(pose)
        self.get_logger().info(f'Navigating to {location_data["name"]} at ({location_data["x"]:.2f}, {location_data["y"]:.2f})')
        self.publish_status_message(f"Going to {location_data['name']}")
    
    def rfid_command_callback(self, msg):
        """RFID 명령어 처리"""
        command = msg.data.strip().lower()
        parts = command.split()
        
        if not parts:
            return
        
        cmd = parts[0]
        
        if cmd == 'list':
            self.list_rfid_mappings()
        elif cmd == 'map' and len(parts) >= 3:
            tag_id = parts[1]
            location_name = ' '.join(parts[2:])
            self.map_rfid_to_location(tag_id, location_name)
        elif cmd == 'unmap' and len(parts) >= 2:
            tag_id = parts[1]
            self.unmap_rfid(tag_id)
        elif cmd == 'clear':
            self.clear_mappings()
        else:
            self.get_logger().warn(f'Unknown command: {command}')
            self.get_logger().info('Available commands: list, map <tag_id> <location_name>, unmap <tag_id>, clear')
    
    def map_rfid_to_location(self, tag_id, location_name):
        """RFID 태그와 위치를 매핑"""
        # location_manager에서 저장된 위치 정보를 가져와야 함
        # 일단 위치 이름만 저장하고, 실제 위치는 location_manager에서 가져오기
        location_data = {
            'name': location_name,
            'x': 0.0,  # 나중에 location_manager에서 가져올 예정
            'y': 0.0,
            'z': 0.0,
            'yaw': 0.0
        }
        
        self.rfid_location_mapping[tag_id] = location_data
        self.save_mappings()
        self.get_logger().info(f'RFID 태그 {tag_id}를 위치 {location_name}에 매핑했습니다')
        self.get_logger().warn('위치 정보는 location_manager에서 가져와야 합니다')
        self.publish_status_message(f"RFID {tag_id} -> {location_name} 매핑 완료")
    
    def unmap_rfid(self, tag_id):
        """RFID 태그 매핑 제거"""
        if tag_id in self.rfid_location_mapping:
            location_name = self.rfid_location_mapping[tag_id]['name']
            del self.rfid_location_mapping[tag_id]
            self.save_mappings()
            self.get_logger().info(f'RFID 태그 {tag_id}의 {location_name} 매핑을 제거했습니다')
            self.publish_status_message(f"RFID {tag_id} 매핑 제거")
        else:
            self.get_logger().warn(f'RFID 태그 {tag_id}의 매핑이 없습니다')
    
    def clear_mappings(self):
        """모든 RFID 매핑 삭제"""
        count = len(self.rfid_location_mapping)
        self.rfid_location_mapping.clear()
        self.save_mappings()
        self.get_logger().info(f'All {count} RFID mappings cleared')
        self.publish_status_message(f"All {count} RFID mappings cleared")
    
    def list_rfid_mappings(self):
        """RFID 태그 매핑 목록 출력"""
        if not self.rfid_location_mapping:
            self.get_logger().info('RFID 태그 매핑이 없습니다')
            return
        
        self.get_logger().info('=== RFID 태그 매핑 목록 ===')
        for tag_id, location_data in self.rfid_location_mapping.items():
            self.get_logger().info(f'  {tag_id} -> {location_data["name"]} ({location_data["x"]:.2f}, {location_data["y"]:.2f})')
        self.get_logger().info('')
    
    def publish_status_message(self, message):
        """상태 메시지 발행"""
        status_msg = String()
        status_msg.data = message
        self.status_pub.publish(status_msg)
    
    def send_location_command(self, command):
        """location_manager로 명령 전송"""
        cmd_msg = String()
        cmd_msg.data = command
        self.location_cmd_pub.publish(cmd_msg)
        self.get_logger().info(f'Location command sent: {command}')


def main(args=None):
    rclpy.init(args=args)
    
    node = RFIDLocationMapper()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
