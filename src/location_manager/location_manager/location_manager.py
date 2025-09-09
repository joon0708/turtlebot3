#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
import yaml
import os
import json
from datetime import datetime
import tf2_ros
import tf2_geometry_msgs
import numpy as np

class LocationManager(Node):
    def __init__(self):
        super().__init__('location_manager')
        
        # 저장 파일 경로 (홈 디렉토리 사용)
        self.config_dir = os.path.expanduser('~/.turtlebot3_locations')
        self.locations_file = os.path.join(self.config_dir, 'saved_locations.yaml')
        
        # 저장된 위치들
        self.saved_locations = {}
        
        # Publishers
        self.nav_goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.status_pub = self.create_publisher(String, '/location_status', 10)
        self.integrated_status_pub = self.create_publisher(String, '/integrated_status', 10)
        self.goal_name_pub = self.create_publisher(String, '/goal_location_name', 10)
        
        # Subscribers
        self.location_cmd_sub = self.create_subscription(String, '/location_command', self.location_command_callback, 10)
        
        # TF2 설정 (현재 위치 가져오기용)
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # 초기화
        self.load_locations()
        self.create_default_locations()
        
        self.get_logger().info('Location Manager initialized')
        self.get_logger().info('Available commands: list, save <name> <x> <y> [yaw], go <name>, delete <name>, clear')
        
    def load_locations(self):
        """저장된 위치 로드"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            if os.path.exists(self.locations_file):
                with open(self.locations_file, 'r', encoding='utf-8') as file:
                    data = yaml.safe_load(file)
                    if data and 'locations' in data:
                        self.saved_locations = data['locations']
                        self.get_logger().info(f'Loaded {len(self.saved_locations)} saved locations')
            else:
                self.get_logger().info('No saved locations file found, creating new one')
        except Exception as e:
            self.get_logger().error(f'Error loading locations: {e}')
            self.saved_locations = {}
    
    def save_locations(self):
        """위치들을 파일에 저장"""
        try:
            data = {
                'locations': self.saved_locations,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.locations_file, 'w', encoding='utf-8') as file:
                yaml.dump(data, file, default_flow_style=False, allow_unicode=True)
            self.get_logger().info(f'Saved {len(self.saved_locations)} locations to {self.locations_file}')
        except Exception as e:
            self.get_logger().error(f'Error saving locations: {e}')
    
    def create_default_locations(self):
        """기본 위치들 생성 (파일이 존재하지 않을 때만)"""
        # 파일이 존재하지 않을 때만 기본 위치 생성
        if not os.path.exists(self.locations_file):
            self.saved_locations = {
                'home': {
                    'name': 'Home',
                    'description': '시작 위치',
                    'x': 0.0,
                    'y': 0.0,
                    'z': 0.0,
                    'yaw': 0.0,
                    'created': datetime.now().isoformat()
                },
                'point_a': {
                    'name': 'Point A',
                    'description': '첫 번째 지점',
                    'x': 1.0,
                    'y': 0.0,
                    'z': 0.0,
                    'yaw': 0.0,
                    'created': datetime.now().isoformat()
                },
                'point_b': {
                    'name': 'Point B',
                    'description': '두 번째 지점',
                    'x': 0.0,
                    'y': 1.0,
                    'z': 0.0,
                    'yaw': 1.57,
                    'created': datetime.now().isoformat()
                }
            }
            self.save_locations()
            self.get_logger().info('Created default locations')
    
    def location_command_callback(self, msg):
        """위치 명령 처리"""
        command = msg.data.strip()
        parts = command.split()
        
        if not parts:
            return
            
        cmd = parts[0].lower()
        
        if cmd == 'list':
            self.list_locations()
        elif cmd == 'save' and len(parts) >= 4:
            name = parts[1]
            try:
                x = float(parts[2])
                y = float(parts[3])
                yaw = float(parts[4]) if len(parts) > 4 else 0.0
                self.save_location(name, x, y, yaw)
            except ValueError:
                self.get_logger().error('Invalid coordinates. Use: save <name> <x> <y> [yaw]')
        elif cmd == 'go' and len(parts) >= 2:
            name = parts[1]
            self.go_to_location(name)
        elif cmd == 'delete' and len(parts) >= 2:
            name = parts[1]
            self.delete_location(name)
        elif cmd == 'clear':
            self.clear_locations()
        elif cmd == 'save_here' and len(parts) >= 2:
            name = parts[1]
            self.save_current_location(name)
        elif cmd == 'status':
            self.publish_status()
        else:
            self.get_logger().warn(f'Unknown command: {command}')
            self.get_logger().info('Available commands: list, save <name> <x> <y> [yaw], save_here <name>, go <name>, delete <name>, clear, status')
    
    def save_location(self, name, x, y, yaw=0.0):
        """새로운 위치 저장"""
        location_id = name.lower().replace(' ', '_')
        
        self.saved_locations[location_id] = {
            'name': name,
            'description': f'Saved location at ({x:.2f}, {y:.2f})',
            'x': x,
            'y': y,
            'z': 0.0,
            'yaw': yaw,
            'created': datetime.now().isoformat()
        }
        
        self.save_locations()
        self.get_logger().info(f'Saved location: {location_id} at ({x:.2f}, {y:.2f}, yaw: {yaw:.2f})')
        self.publish_status_message(f"Saved location: {location_id}")
    
    def save_current_location(self, name):
        """현재 로봇 위치를 저장"""
        try:
            # base_link에서 map으로의 변환 가져오기
            transform = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
            
            # 현재 위치 추출
            x = transform.transform.translation.x
            y = transform.transform.translation.y
            z = transform.transform.translation.z
            
            # 현재 방향 (quaternion을 yaw로 변환)
            orientation = transform.transform.rotation
            yaw = self.quaternion_to_yaw(orientation)
            
            # 위치 저장
            self.save_location(name, x, y, yaw)
            
        except Exception as e:
            self.get_logger().error(f'Failed to get current location: {e}')
            self.get_logger().info('Make sure TF is available and robot is localized')
    
    def quaternion_to_yaw(self, orientation):
        """quaternion을 yaw 각도로 변환"""
        # quaternion을 euler angles로 변환
        siny_cosp = 2 * (orientation.w * orientation.z + orientation.x * orientation.y)
        cosy_cosp = 1 - 2 * (orientation.y * orientation.y + orientation.z * orientation.z)
        yaw = np.arctan2(siny_cosp, cosy_cosp)
        return float(yaw)  # numpy 객체를 일반 Python float로 변환
    
    def go_to_location(self, name):
        """저장된 위치로 이동"""
        location_id = name.lower().replace(' ', '_')
        
        if location_id not in self.saved_locations:
            self.get_logger().warn(f'Location not found: {name}')
            return
        
        location = self.saved_locations[location_id]
        
        # PoseStamped 메시지 생성
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        
        pose.pose.position.x = location['x']
        pose.pose.position.y = location['y']
        pose.pose.position.z = location['z']
        
        # yaw를 quaternion으로 변환
        yaw = location['yaw']
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = np.sin(yaw / 2.0)
        pose.pose.orientation.w = np.cos(yaw / 2.0)
        
        # 네비게이션 목표 발행
        self.nav_goal_pub.publish(pose)
        self.get_logger().info(f'Navigating to {location_id}: {location["name"]} at ({location["x"]:.2f}, {location["y"]:.2f})')
        self.publish_status_message(f"Going to {location_id}")
        
        # LCD에 목표 위치 이름 전달
        self.publish_goal_name_to_lcd(location['name'])
    
    def delete_location(self, name):
        """위치 삭제"""
        location_id = name.lower().replace(' ', '_')
        
        if location_id in self.saved_locations:
            removed = self.saved_locations.pop(location_id)
            self.save_locations()
            self.get_logger().info(f'Deleted location: {location_id} - {removed["name"]}')
            self.publish_status_message(f"Deleted location: {location_id}")
        else:
            self.get_logger().warn(f'Location not found: {name}')
    
    def clear_locations(self):
        """모든 위치 삭제"""
        count = len(self.saved_locations)
        self.saved_locations.clear()
        self.save_locations()
        self.get_logger().info(f'Cleared all {count} locations')
        self.publish_status_message(f"Cleared all locations")
    
    def list_locations(self):
        """저장된 위치 목록 출력"""
        if not self.saved_locations:
            message = 'No saved locations'
            self.get_logger().info(message)
            self.publish_status_message(message)
            return
        
        # 간결한 메시지로 토픽 발행
        message = f'Saved Locations ({len(self.saved_locations)}): '
        location_list = []
        for location_id, location in self.saved_locations.items():
            location_list.append(f'{location_id}({location["x"]:.1f},{location["y"]:.1f})')
        message += ', '.join(location_list)
        
        # 상세 정보는 로그에만 출력
        self.get_logger().info(f'\n=== Saved Locations ({len(self.saved_locations)}) ===')
        for location_id, location in self.saved_locations.items():
            self.get_logger().info(f'{location_id}: {location["name"]}')
            self.get_logger().info(f'  Position: ({location["x"]:.2f}, {location["y"]:.2f})')
            self.get_logger().info(f'  Yaw: {location["yaw"]:.2f}')
            self.get_logger().info(f'  Created: {location["created"]}')
            self.get_logger().info('')
        
        self.publish_status_message(message)
    
    def publish_status(self):
        """상태 정보 발행"""
        status = f"Ready - {len(self.saved_locations)} locations saved"
        self.publish_status_message(status)
    
    def publish_status_message(self, message):
        """상태 메시지 발행"""
        status_msg = String()
        status_msg.data = message
        self.status_pub.publish(status_msg)
        
        # 통합 상태도 함께 발행
        self.publish_integrated_status(message)
    
    def publish_integrated_status(self, location_message):
        """통합 상태 발행"""
        integrated_msg = String()
        integrated_msg.data = location_message
        self.integrated_status_pub.publish(integrated_msg)
    
    def publish_goal_name_to_lcd(self, location_name):
        """LCD에 목표 위치 이름 발행"""
        goal_name_msg = String()
        goal_name_msg.data = location_name
        self.goal_name_pub.publish(goal_name_msg)
        self.get_logger().info(f'Goal location name sent to LCD: {location_name}')
    


def main(args=None):
    rclpy.init(args=args)
    location_manager = LocationManager()
    
    try:
        rclpy.spin(location_manager)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        location_manager.get_logger().error(f'Error in location_manager: {e}')
    finally:
        try:
            location_manager.destroy_node()
        except:
            pass
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()
