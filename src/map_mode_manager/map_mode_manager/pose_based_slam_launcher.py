#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped
from std_msgs.msg import String
import subprocess
import os
import signal
import time

class PoseBasedSLAMLauncher(Node):
    """영점 지정 시 해당 영점을 기준으로 SLAM을 시작하는 노드"""
    
    def __init__(self):
        super().__init__('pose_based_slam_launcher')
        
        # 파라미터
        self.declare_parameter('slam_start_delay', 2.0)  # 영점 지정 후 SLAM 시작 지연 시간
        self.slam_start_delay = self.get_parameter('slam_start_delay').value
        
        # 상태 변수
        self.initial_pose_received = False
        self.slam_started = False
        self.cartographer_process = None
        
        # 구독자
        self.initial_pose_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/initialpose',
            self.initial_pose_callback,
            10
        )
        
        # 발행자
        self.status_pub = self.create_publisher(
            String,
            '/slam_status',
            10
        )
        
        # 타이머
        self.slam_start_timer = None
        
        self.get_logger().info('Pose-based SLAM Launcher 노드가 시작되었습니다.')
        self.get_logger().info('영점이 지정되면 {}초 후 SLAM을 시작합니다.'.format(self.slam_start_delay))
        self.publish_status("영점 대기 중...")
    
    def initial_pose_callback(self, msg: PoseWithCovarianceStamped):
        """영점 지정 콜백"""
        if not self.initial_pose_received:
            self.initial_pose_received = True
            self.get_logger().info('영점이 지정되었습니다!')
            self.get_logger().info('위치: ({:.2f}, {:.2f})'.format(
                msg.pose.pose.position.x, 
                msg.pose.pose.position.y
            ))
            
            # SLAM 시작 타이머 시작
            self.slam_start_timer = self.create_timer(
                self.slam_start_delay,
                self.start_slam
            )
            
            self.publish_status("SLAM 시작 준비 중...")
        else:
            self.get_logger().warn('영점이 이미 지정되었습니다. SLAM을 재시작합니다.')
            self.restart_slam()
    
    def start_slam(self):
        """SLAM 시작"""
        if not self.slam_started:
            self.slam_started = True
            
            try:
                # 카토그래퍼 노드 시작
                self.launch_cartographer()
                self.get_logger().info('SLAM이 시작되었습니다!')
                self.publish_status("SLAM 실행 중")
                
                # 타이머 정리
                if self.slam_start_timer:
                    self.slam_start_timer.cancel()
                    self.slam_start_timer = None
                    
            except Exception as e:
                self.get_logger().error(f'SLAM 시작 실패: {e}')
                self.publish_status("SLAM 시작 실패")
    
    def launch_cartographer(self):
        """카토그래퍼 노드 실행"""
        # 카토그래퍼 설정 파일 경로
        config_dir = os.path.join(
            os.environ.get('AMENT_PREFIX_PATH', '/opt/ros/humble'),
            'share', 'turtlebot3_cartographer', 'config'
        )
        
        # 카토그래퍼 노드 실행 명령
        cmd = [
            'ros2', 'run', 'cartographer_ros', 'cartographer_node',
            '-configuration_directory', config_dir,
            '-configuration_basename', 'turtlebot3_lds_2d.lua'
        ]
        
        # 환경 변수 설정
        env = os.environ.copy()
        env['ROS_DOMAIN_ID'] = '10'
        env['USE_SIM_TIME'] = 'false'
        
        # 프로세스 시작
        self.cartographer_process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        self.get_logger().info(f'카토그래퍼 프로세스 시작됨 (PID: {self.cartographer_process.pid})')
    
    def restart_slam(self):
        """SLAM 재시작"""
        if self.cartographer_process:
            try:
                # 기존 프로세스 종료
                os.killpg(os.getpgid(self.cartographer_process.pid), signal.SIGTERM)
                self.cartographer_process.wait(timeout=5)
                self.get_logger().info('기존 카토그래퍼 프로세스가 종료되었습니다.')
            except:
                self.get_logger().warn('기존 카토그래퍼 프로세스 종료 실패')
        
        # 상태 리셋
        self.slam_started = False
        self.cartographer_process = None
        
        # SLAM 재시작
        self.slam_start_timer = self.create_timer(
            self.slam_start_delay,
            self.start_slam
        )
        
        self.publish_status("SLAM 재시작 준비 중...")
    
    def publish_status(self, status: str):
        """상태 발행"""
        msg = String()
        msg.data = status
        self.status_pub.publish(msg)
    
    def destroy_node(self):
        """노드 종료 시 정리"""
        if self.cartographer_process:
            try:
                os.killpg(os.getpgid(self.cartographer_process.pid), signal.SIGTERM)
                self.cartographer_process.wait(timeout=5)
            except:
                pass
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = PoseBasedSLAMLauncher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        node.get_logger().error(f'오류 발생: {e}')
    finally:
        try:
            node.destroy_node()
        except:
            pass
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()
