#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'return_x',
            default_value='0.0',
            description='복귀 목표의 X 좌표'),

        DeclareLaunchArgument(
            'return_y',
            default_value='0.0',
            description='복귀 목표의 Y 좌표'),

        DeclareLaunchArgument(
            'return_z',
            default_value='0.0',
            description='복귀 목표의 Z 방향 (quaternion)'),

        DeclareLaunchArgument(
            'return_w',
            default_value='1.0',
            description='복귀 목표의 W 방향 (quaternion)'),

        DeclareLaunchArgument(
            'rfid_topic',
            default_value='/rfid/tag',
            description='RFID 태그 토픽 이름'),

        DeclareLaunchArgument(
            'frame_id',
            default_value='map',
            description='좌표계 프레임 ID'),

        DeclareLaunchArgument(
            'cooldown_sec',
            default_value='5.0',
            description='RFID 태그 감지 후 쿨다운 시간 (초)'),

        DeclareLaunchArgument(
            'max_retries',
            default_value='3',
            description='네비게이션 실패 시 최대 재시도 횟수'),

        DeclareLaunchArgument(
            'retry_delay_sec',
            default_value='1.0',
            description='재시도 간 딜레이 시간 (초)'),

        Node(
            package='rfid_return_navigation',
            executable='rfid_return_navigation',
            name='rfid_return_navigation',
            parameters=[{
                'return_x': LaunchConfiguration('return_x'),
                'return_y': LaunchConfiguration('return_y'),
                'return_z': LaunchConfiguration('return_z'),
                'return_w': LaunchConfiguration('return_w'),
                'rfid_topic': LaunchConfiguration('rfid_topic'),
                'frame_id': LaunchConfiguration('frame_id'),
                'cooldown_sec': LaunchConfiguration('cooldown_sec'),
                'max_retries': LaunchConfiguration('max_retries'),
                'retry_delay_sec': LaunchConfiguration('retry_delay_sec'),
            }],
            output='screen'),
    ])
