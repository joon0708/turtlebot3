#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav2_msgs.srv import SaveMap
from std_msgs.msg import String
import time
import os

class MapUpdater(Node):
    def __init__(self):
        super().__init__('map_updater')
        
        # 맵 저장 서비스 클라이언트
        self.save_map_client = self.create_client(SaveMap, '/map_saver/save_map')
        
        # 상태 발행
        self.status_pub = self.create_publisher(String, '/map_update_status', 10)
        
        # 맵 저장 타이머 (30초마다 자동 저장)
        self.save_timer = self.create_timer(30.0, self.auto_save_map)
        
        # 맵 저장 디렉토리
        self.map_dir = '/root/turtlebot3/install/turtlebot3_navigation2/share/turtlebot3_navigation2/map'
        
        self.get_logger().info('Map Updater 노드가 시작되었습니다.')
        self.get_logger().info('30초마다 자동으로 맵을 저장합니다.')
        self.publish_status("맵 업데이터 시작됨")
    
    def auto_save_map(self):
        """자동 맵 저장"""
        try:
            if self.save_map_client.wait_for_service(timeout_sec=5.0):
                # 현재 시간으로 파일명 생성
                timestamp = int(time.time())
                map_name = f"updated_map_{timestamp}"
                
                request = SaveMap.Request()
                request.map_url = os.path.join(self.map_dir, map_name)
                
                future = self.save_map_client.call_async(request)
                self.get_logger().info(f'맵 저장 요청: {map_name}')
                self.publish_status(f"맵 저장 중: {map_name}")
                
                # 응답 처리
                rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)
                
                if future.result() is not None:
                    response = future.result()
                    if response.result == SaveMap.Response().RESULT_SUCCESS:
                        self.get_logger().info(f'맵 저장 성공: {map_name}')
                        self.publish_status(f"맵 저장 완료: {map_name}")
                        
                        # 기존 맵 파일을 새 맵으로 교체
                        self.replace_current_map(map_name)
                    else:
                        self.get_logger().error(f'맵 저장 실패: {map_name}')
                        self.publish_status("맵 저장 실패")
                else:
                    self.get_logger().error('맵 저장 서비스 응답 없음')
                    self.publish_status("맵 저장 서비스 응답 없음")
            else:
                self.get_logger().warn('맵 저장 서비스를 찾을 수 없습니다.')
                self.publish_status("맵 저장 서비스 없음")
                
        except Exception as e:
            self.get_logger().error(f'맵 저장 중 오류: {e}')
            self.publish_status(f"맵 저장 오류: {e}")
    
    def replace_current_map(self, new_map_name):
        """현재 맵을 새 맵으로 교체"""
        try:
            # 기존 맵 파일 백업
            old_map_yaml = os.path.join(self.map_dir, 'map.yaml')
            old_map_pgm = os.path.join(self.map_dir, 'map.pgm')
            
            if os.path.exists(old_map_yaml):
                os.rename(old_map_yaml, os.path.join(self.map_dir, 'map_backup.yaml'))
            if os.path.exists(old_map_pgm):
                os.rename(old_map_pgm, os.path.join(self.map_dir, 'map_backup.pgm'))
            
            # 새 맵 파일을 현재 맵으로 복사
            new_map_yaml = os.path.join(self.map_dir, f'{new_map_name}.yaml')
            new_map_pgm = os.path.join(self.map_dir, f'{new_map_name}.pgm')
            
            if os.path.exists(new_map_yaml):
                os.rename(new_map_yaml, old_map_yaml)
            if os.path.exists(new_map_pgm):
                os.rename(new_map_pgm, old_map_pgm)
            
            self.get_logger().info('맵 파일 교체 완료')
            self.publish_status("맵 파일 교체 완료")
            
        except Exception as e:
            self.get_logger().error(f'맵 파일 교체 중 오류: {e}')
            self.publish_status(f"맵 파일 교체 오류: {e}")
    
    def publish_status(self, message):
        """상태 메시지 발행"""
        msg = String()
        msg.data = message
        self.status_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = MapUpdater()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
