#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from std_msgs.msg import String, Bool
from rcl_interfaces.msg import Parameter, ParameterValue, ParameterType
from rcl_interfaces.srv import SetParameters, GetParameters
import os
import time
from typing import Optional, Dict, Any


class ModeSwitcher(Node):
    """
    실제 모드 전환을 수행하고 Cartographer 파라미터를 관리하는 노드
    
    MapSimilarityChecker에서 모드 전환 요청을 받아
    Cartographer의 파라미터 파일을 동적으로 변경합니다.
    """
    
    def __init__(self):
        super().__init__('mode_switcher')
        
        # QoS 설정
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )
        
        # 파라미터 설정
        self.declare_parameters(
            namespace='',
            parameters=[
                ('slam_config_file', 'turtlebot3_lds_2d.lua'),           # SLAM 모드 설정 파일
                ('localization_config_file', 'turtlebot3_lds_2d_localization.lua'),  # Localization 모드 설정 파일
                ('cartographer_node_name', 'cartographer_node'),         # Cartographer 노드 이름
                ('config_directory', '/root/turtlebot3/install/turtlebot3_cartographer/share/turtlebot3_cartographer/config'),  # 설정 파일 디렉토리
                ('mode_switch_timeout', 10.0),                          # 모드 전환 타임아웃 (초)
                ('enable_parameter_validation', True),                  # 파라미터 검증 활성화
            ]
        )
        
        # 파라미터 로드
        self.slam_config_file = self.get_parameter('slam_config_file').value
        self.localization_config_file = self.get_parameter('localization_config_file').value
        self.cartographer_node_name = self.get_parameter('cartographer_node_name').value
        self.config_directory = self.get_parameter('config_directory').value
        self.mode_switch_timeout = self.get_parameter('mode_switch_timeout').value
        self.enable_parameter_validation = self.get_parameter('enable_parameter_validation').value
        
        # 구독자 및 발행자
        self.mode_sub = self.create_subscription(
            String, 'current_mode', self.mode_callback, qos_profile
        )
        self.switch_request_sub = self.create_subscription(
            Bool, 'mode_switch_request', self.switch_request_callback, qos_profile
        )
        
        # 발행자
        self.mode_status_pub = self.create_publisher(String, 'mode_status', qos_profile)
        self.switch_result_pub = self.create_publisher(Bool, 'switch_result', qos_profile)
        
        # 서비스 클라이언트
        self.set_params_client = self.create_client(SetParameters, f'/{self.cartographer_node_name}/set_parameters')
        self.get_params_client = self.create_client(GetParameters, f'/{self.cartographer_node_name}/get_parameters')
        
        # 상태 변수
        self.current_mode = 'SLAM'  # 초기 모드
        self.target_mode = None
        self.is_switching = False
        self.last_switch_time = 0.0
        self.switch_success_count = 0
        self.switch_failure_count = 0
        
        # 모드별 설정 파일 매핑
        self.mode_config_files = {
            'SLAM': self.slam_config_file,
            'Localization': self.localization_config_file
        }
        
        # 모드별 파라미터 설정
        self.mode_parameters = {
            'SLAM': {
                'submap_publish_period_sec': 0.3,
                'pose_publish_period_sec': 5e-3,
                'trajectory_publish_period_sec': 30e-3,
                'use_online_correlative_scan_matching': True
            },
            'Localization': {
                'submap_publish_period_sec': 2.0,
                'pose_publish_period_sec': 0.1,
                'trajectory_publish_period_sec': 0.5,
                'use_online_correlative_scan_matching': False
            }
        }
        
        # 초기 상태 발행
        self.publish_mode_status()
        
        self.get_logger().info(
            f'ModeSwitcher 노드가 초기화되었습니다. '
            f'SLAM 설정: {self.slam_config_file}, '
            f'Localization 설정: {self.localization_config_file}'
        )
    
    def mode_callback(self, msg: String):
        """현재 모드 콜백"""
        new_mode = msg.data
        if new_mode != self.current_mode:
            self.get_logger().info(f'모드 변경 감지: {self.current_mode} → {new_mode}')
            self.current_mode = new_mode
            self.publish_mode_status()
    
    def switch_request_callback(self, msg: Bool):
        """모드 전환 요청 콜백"""
        if msg.data and not self.is_switching:
            self.get_logger().info('모드 전환 요청을 받았습니다.')
            self.initiate_mode_switch()
    
    def initiate_mode_switch(self):
        """모드 전환을 시작합니다."""
        if self.is_switching:
            self.get_logger().warn('이미 모드 전환 중입니다.')
            return
        
        # 전환할 모드 결정
        if self.current_mode == 'SLAM':
            target_mode = 'Localization'
        else:
            target_mode = 'SLAM'
        
        self.target_mode = target_mode
        self.is_switching = True
        self.last_switch_time = time.time()
        
        self.get_logger().info(f'모드 전환 시작: {self.current_mode} → {target_mode}')
        
        # 모드 전환 수행
        self.perform_mode_switch(target_mode)
    
    def perform_mode_switch(self, target_mode: str):
        """실제 모드 전환을 수행합니다."""
        try:
            # 1단계: 설정 파일 변경
            config_file = self.mode_config_files[target_mode]
            config_path = os.path.join(self.config_directory, config_file)
            
            if not os.path.exists(config_path):
                self.get_logger().error(f'설정 파일이 존재하지 않습니다: {config_path}')
                self.switch_failed(f'설정 파일 없음: {config_file}')
                return
            
            # 2단계: Cartographer 파라미터 변경
            if not self.update_cartographer_parameters(target_mode):
                self.switch_failed('Cartographer 파라미터 변경 실패')
                return
            
            # 3단계: 모드 전환 완료
            self.switch_successful(target_mode)
            
        except Exception as e:
            self.get_logger().error(f'모드 전환 중 오류 발생: {e}')
            self.switch_failed(f'오류: {str(e)}')
    
    def update_cartographer_parameters(self, target_mode: str) -> bool:
        """Cartographer 노드의 파라미터를 업데이트합니다."""
        try:
            # 파라미터 변경 요청 준비
            parameters = []
            mode_params = self.mode_parameters[target_mode]
            
            for param_name, param_value in mode_params.items():
                param = Parameter()
                param.name = param_name
                param.value.type = ParameterType.DOUBLE
                param.value.double_value = float(param_value)
                parameters.append(param)
            
            # 파라미터 변경 요청
            request = SetParameters.Request()
            request.parameters = parameters
            
            # 서비스 호출
            if not self.set_params_client.wait_for_service(timeout_sec=5.0):
                self.get_logger().error('SetParameters 서비스를 찾을 수 없습니다.')
                return False
            
            future = self.set_params_client.call_async(request)
            
            # 응답 대기
            rclpy.spin_until_future_complete(self, future, timeout_sec=self.mode_switch_timeout)
            
            if future.done():
                response = future.result()
                if response.results[0].successful:
                    self.get_logger().info(f'Cartographer 파라미터 변경 성공: {target_mode}')
                    return True
                else:
                    self.get_logger().error(f'파라미터 변경 실패: {response.results[0].reason}')
                    return False
            else:
                self.get_logger().error('파라미터 변경 서비스 타임아웃')
                return False
                
        except Exception as e:
            self.get_logger().error(f'파라미터 변경 중 오류: {e}')
            return False
    
    def switch_successful(self, new_mode: str):
        """모드 전환이 성공했습니다."""
        old_mode = self.current_mode
        self.current_mode = new_mode
        self.is_switching = False
        self.switch_success_count += 1
        
        # 성공 결과 발행
        result_msg = Bool()
        result_msg.data = True
        self.switch_result_pub.publish(result_msg)
        
        # 모드 상태 발행
        self.publish_mode_status()
        
        # 로깅
        self.get_logger().info(
            f'모드 전환 성공: {old_mode} → {new_mode} '
            f'(성공 횟수: {self.switch_success_count})'
        )
    
    def switch_failed(self, reason: str):
        """모드 전환이 실패했습니다."""
        self.is_switching = False
        self.switch_failure_count += 1
        
        # 실패 결과 발행
        result_msg = Bool()
        result_msg.data = False
        self.switch_result_pub.publish(result_msg)
        
        # 로깅
        self.get_logger().error(
            f'모드 전환 실패: {reason} '
            f'(실패 횟수: {self.switch_failure_count})'
        )
    
    def publish_mode_status(self):
        """현재 모드 상태를 발행합니다."""
        status_msg = String()
        if self.is_switching:
            status_msg.data = f'SWITCHING_{self.current_mode}_TO_{self.target_mode}'
        else:
            status_msg.data = f'STABLE_{self.current_mode}'
        
        self.mode_status_pub.publish(status_msg)
    
    def get_current_mode(self) -> str:
        """현재 모드를 반환합니다."""
        return self.current_mode
    
    def is_mode_switching(self) -> bool:
        """모드 전환 중인지 확인합니다."""
        return self.is_switching
    
    def get_switch_statistics(self) -> Dict[str, Any]:
        """모드 전환 통계를 반환합니다."""
        return {
            'current_mode': self.current_mode,
            'is_switching': self.is_switching,
            'success_count': self.switch_success_count,
            'failure_count': self.switch_failure_count,
            'last_switch_time': self.last_switch_time
        }
    
    def validate_config_files(self) -> bool:
        """설정 파일들의 유효성을 검증합니다."""
        if not self.enable_parameter_validation:
            return True
        
        for mode, config_file in self.mode_config_files.items():
            config_path = os.path.join(self.config_directory, config_file)
            if not os.path.exists(config_path):
                self.get_logger().error(f'{mode} 모드 설정 파일이 존재하지 않습니다: {config_path}')
                return False
        
        self.get_logger().info('모든 설정 파일이 유효합니다.')
        return True


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = ModeSwitcher()
        
        # 설정 파일 검증
        if not node.validate_config_files():
            node.get_logger().error('설정 파일 검증 실패. 노드를 종료합니다.')
            return
        
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
