#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from std_msgs.msg import Float32, String, Bool
from geometry_msgs.msg import PoseStamped
import numpy as np
from typing import Optional, List
import time


class MapSimilarityChecker(Node):
    """
    맵 유사도를 체크하고 모드 전환을 결정하는 노드
    
    MapComparator에서 받은 유사도 점수를 분석하여
    SLAM 모드와 Localization 모드 간의 전환을 결정합니다.
    """
    
    def __init__(self):
        super().__init__('map_similarity_checker')
        
        # QoS 설정 (호환성 향상)
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )
        
        # 파라미터 설정
        self.declare_parameters(
            namespace='',
            parameters=[
                ('similarity_threshold', 0.8),      # 유사도 임계값 (0.0 ~ 1.0)
                ('check_interval', 5.0),            # 체크 주기 (초)
                ('mode_switch_delay', 2.0),         # 모드 전환 후 대기 시간 (초)
                ('min_samples_for_decision', 3),    # 결정을 위한 최소 샘플 수
                ('similarity_window_size', 10),     # 유사도 점수 윈도우 크기
                ('stability_threshold', 0.1),       # 안정성 임계값
            ]
        )
        
        # 파라미터 로드
        self.similarity_threshold = self.get_parameter('similarity_threshold').value
        self.check_interval = self.get_parameter('check_interval').value
        self.mode_switch_delay = self.get_parameter('mode_switch_delay').value
        self.min_samples_for_decision = self.get_parameter('min_samples_for_decision').value
        self.similarity_window_size = self.get_parameter('similarity_window_size').value
        self.stability_threshold = self.get_parameter('stability_threshold').value
        
        # 구독자 및 발행자
        self.similarity_sub = self.create_subscription(
            Float32, 'map_similarity_score', self.similarity_callback, qos_profile
        )
        
        # 발행자
        self.mode_pub = self.create_publisher(String, 'current_mode', qos_profile)
        self.mode_switch_pub = self.create_publisher(Bool, 'mode_switch_request', qos_profile)
        self.similarity_analysis_pub = self.create_publisher(Float32, 'similarity_analysis', qos_profile)
        self.similarity_status_pub = self.create_publisher(String, 'map_similarity_status', qos_profile)
        
        # 상태 변수
        self.current_mode = 'SLAM'  # 초기 모드
        self.similarity_scores = []  # 유사도 점수 히스토리
        self.last_mode_switch_time = 0.0
        self.mode_switch_count = 0
        self.is_stable = False
        
        # 타이머 설정
        self.analysis_timer = self.create_timer(self.check_interval, self.analyze_similarity)
        
        # 초기 모드 발행
        self.publish_current_mode()
        
        self.get_logger().info(
            f'MapSimilarityChecker 노드가 초기화되었습니다. '
            f'임계값: {self.similarity_threshold}, '
            f'체크 주기: {self.check_interval}초'
        )
    
    def similarity_callback(self, msg: Float32):
        """맵 유사도 점수 콜백"""
        similarity_score = msg.data
        
        # 유효한 점수인지 확인 (0.0 ~ 1.0)
        if 0.0 <= similarity_score <= 1.0:
            self.similarity_scores.append(similarity_score)
            
            # 윈도우 크기 유지
            if len(self.similarity_scores) > self.similarity_window_size:
                self.similarity_scores.pop(0)
            
            # 맵 변화 감지 상태 발행
            self.publish_similarity_status(similarity_score)
            
            self.get_logger().debug(f'새로운 유사도 점수: {similarity_score:.3f}')
        else:
            self.get_logger().warn(f'잘못된 유사도 점수: {similarity_score}')
    
    def publish_similarity_status(self, similarity_score: float):
        """맵 유사도 상태를 발행합니다."""
        status_msg = String()
        
        # 유사도에 따른 상태 메시지 생성
        if similarity_score < self.similarity_threshold:
            status_msg.data = f'CHANGE_DETECTED:{similarity_score:.3f}'
        else:
            status_msg.data = f'SIMILARITY:{similarity_score:.3f}'
        
        self.similarity_status_pub.publish(status_msg)
    
    def calculate_stability(self) -> float:
        """유사도 점수의 안정성을 계산합니다."""
        if len(self.similarity_scores) < 2:
            return 0.0
        
        # 표준편차 계산
        std_dev = np.std(self.similarity_scores)
        
        # 안정성 점수 (표준편차가 낮을수록 안정적)
        stability = max(0.0, 1.0 - std_dev)
        
        return stability
    
    def calculate_trend(self) -> float:
        """유사도 점수의 추세를 계산합니다."""
        if len(self.similarity_scores) < 2:
            return 0.0
        
        # 선형 회귀로 추세 계산
        x = np.arange(len(self.similarity_scores))
        y = np.array(self.similarity_scores)
        
        # 기울기 계산
        slope = np.polyfit(x, y, 1)[0]
        
        # 추세 점수 (-1.0 ~ 1.0)
        trend = np.tanh(slope * 10)  # 기울기를 -1 ~ 1 범위로 정규화
        
        return trend
    
    def should_switch_mode(self) -> tuple[bool, str]:
        """모드 전환이 필요한지 결정합니다."""
        if len(self.similarity_scores) < self.min_samples_for_decision:
            return False, "샘플 수 부족"
        
        # 현재 시간 확인
        current_time = time.time()
        if current_time - self.last_mode_switch_time < self.mode_switch_delay:
            return False, "전환 대기 시간"
        
        # 평균 유사도 점수 계산
        avg_similarity = np.mean(self.similarity_scores)
        
        # 안정성 계산
        stability = self.calculate_stability()
        self.is_stable = stability >= self.stability_threshold
        
        # 추세 계산
        trend = self.calculate_trend()
        
        # 모드 전환 결정 로직
        if self.current_mode == 'SLAM':
            # SLAM 모드에서 Localization 모드로 전환
            if (avg_similarity >= self.similarity_threshold and 
                self.is_stable and trend >= 0.0):
                return True, "Localization"
        else:  # Localization 모드
            # Localization 모드에서 SLAM 모드로 전환
            if (avg_similarity < self.similarity_threshold or 
                not self.is_stable or trend < -0.3):
                return True, "SLAM"
        
        return False, "전환 불필요"
    
    def switch_mode(self, new_mode: str):
        """모드를 전환합니다."""
        if new_mode == self.current_mode:
            return
        
        old_mode = self.current_mode
        self.current_mode = new_mode
        self.last_mode_switch_time = time.time()
        self.mode_switch_count += 1
        
        # 모드 전환 요청 발행
        switch_request = Bool()
        switch_request.data = True
        self.mode_switch_pub.publish(switch_request)
        
        # 현재 모드 발행
        self.publish_current_mode()
        
        # 로깅
        self.get_logger().info(
            f'모드 전환: {old_mode} → {new_mode} '
            f'(전환 횟수: {self.mode_switch_count})'
        )
        
        # 유사도 점수 히스토리 초기화
        self.similarity_scores.clear()
    
    def publish_current_mode(self):
        """현재 모드를 발행합니다."""
        mode_msg = String()
        mode_msg.data = self.current_mode
        self.mode_pub.publish(mode_msg)
    
    def analyze_similarity(self):
        """주기적으로 유사도를 분석하고 모드 전환을 결정합니다."""
        if not self.similarity_scores:
            return
        
        # 모드 전환 필요성 확인
        should_switch, reason = self.should_switch_mode()
        
        if should_switch:
            # 새로운 모드 결정
            if self.current_mode == 'SLAM':
                new_mode = 'Localization'
            else:
                new_mode = 'SLAM'
            
            # 모드 전환
            self.switch_mode(new_mode)
        else:
            # 모드 전환 불필요
            self.get_logger().debug(f'모드 전환 불필요: {reason}')
        
        # 분석 결과 발행
        if self.similarity_scores:
            avg_similarity = np.mean(self.similarity_scores)
            stability = self.calculate_stability()
            trend = self.calculate_trend()
            
            # 분석 결과 로깅
            self.get_logger().info(
                f'현재 모드: {self.current_mode}, '
                f'평균 유사도: {avg_similarity:.3f}, '
                f'안정성: {stability:.3f}, '
                f'추세: {trend:.3f}'
            )
            
            # 분석 결과 발행
            analysis_msg = Float32()
            analysis_msg.data = avg_similarity
            self.similarity_analysis_pub.publish(analysis_msg)
    
    def get_current_mode(self) -> str:
        """현재 모드를 반환합니다."""
        return self.current_mode
    
    def get_similarity_stats(self) -> dict:
        """유사도 통계를 반환합니다."""
        if not self.similarity_scores:
            return {
                'count': 0,
                'mean': 0.0,
                'std': 0.0,
                'min': 0.0,
                'max': 0.0,
                'stability': 0.0,
                'trend': 0.0
            }
        
        scores = np.array(self.similarity_scores)
        
        return {
            'count': len(scores),
            'mean': float(np.mean(scores)),
            'std': float(np.std(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores)),
            'stability': float(self.calculate_stability()),
            'trend': float(self.calculate_trend())
        }


def main(args=None):
    rclpy.init(args=args)
    node = None
    
    try:
        node = MapSimilarityChecker()
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node:
            node.get_logger().info('키보드 인터럽트로 노드를 종료합니다.')
    except Exception as e:
        if node:
            node.get_logger().error(f'노드 실행 중 오류 발생: {e}')
    finally:
        if node:
            try:
                node.destroy_node()
            except Exception as e:
                print(f'노드 파괴 중 오류: {e}')
        
        if rclpy.ok():
            try:
                rclpy.shutdown()
            except Exception as e:
                print(f'ROS2 종료 중 오류: {e}')


if __name__ == '__main__':
    main()
