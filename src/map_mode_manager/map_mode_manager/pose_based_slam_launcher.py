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
        
        # 초기 포즈 저장용
        self.last_initial_pose = None
        
        self.get_logger().info('Pose-based SLAM Launcher 노드가 시작되었습니다.')
        self.get_logger().info('영점이 지정되면 {}초 후 SLAM을 시작합니다.'.format(self.slam_start_delay))
        self.publish_status("영점 대기 중...")
    
    def initial_pose_callback(self, msg: PoseWithCovarianceStamped):
        """영점 지정 콜백"""
        # 초기 포즈 저장
        self.last_initial_pose = msg.pose.pose
        
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
        """카토그래퍼를 SLAM 모드로 전환"""
        try:
            # 카토그래퍼 서비스 클라이언트 생성
            from cartographer_ros_msgs.srv import StartTrajectory, FinishTrajectory
            
            # 기존 trajectory 종료 (로컬라이제이션 모드)
            finish_client = self.create_client(FinishTrajectory, '/finish_trajectory')
            if finish_client.wait_for_service(timeout_sec=5.0):
                finish_req = FinishTrajectory.Request()
                finish_req.trajectory_id = 0  # 기본 trajectory ID
                finish_future = finish_client.call_async(finish_req)
                self.get_logger().info('기존 로컬라이제이션 trajectory를 종료합니다.')
                
                # 잠시 대기
                time.sleep(1.0)
            
            # 새로운 SLAM trajectory 시작
            start_client = self.create_client(StartTrajectory, '/start_trajectory')
            if start_client.wait_for_service(timeout_sec=5.0):
                start_req = StartTrajectory.Request()
                start_req.configuration_directory = os.path.join(
                    get_package_share_directory('turtlebot3_cartographer'), 'config')
                start_req.configuration_basename = 'turtlebot3_lds_2d.lua'  # SLAM 설정
                start_req.use_initial_pose = True
                start_req.initial_pose = self.last_initial_pose
                start_req.relative_to_trajectory_id = 0
                
                start_future = start_client.call_async(start_req)
                self.get_logger().info('새로운 SLAM trajectory를 시작합니다.')
                self.get_logger().info(f'초기 포즈: ({self.last_initial_pose.position.x:.2f}, {self.last_initial_pose.position.y:.2f})')
            else:
                self.get_logger().error('카토그래퍼 서비스를 찾을 수 없습니다.')
                
        except Exception as e:
            self.get_logger().error(f'카토그래퍼 SLAM 모드 전환 실패: {e}')
    
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
