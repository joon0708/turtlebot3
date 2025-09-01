# Copyright 2019 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Darby Lim

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node

TURTLEBOT3_MODEL = os.environ['TURTLEBOT3_MODEL']
ROS_DISTRO = os.environ.get('ROS_DISTRO')


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    start_rviz = LaunchConfiguration('start_rviz', default='false')
    map_dir = LaunchConfiguration(
        'map',
        default=os.path.join(
            get_package_share_directory('turtlebot3_navigation2'),
            'map',
            'map.yaml'))

    param_file_name = TURTLEBOT3_MODEL + '.yaml'
    if ROS_DISTRO == 'humble':
        param_dir = LaunchConfiguration(
            'params_file',
            default=os.path.join(
                get_package_share_directory('turtlebot3_navigation2'),
                'param',
                ROS_DISTRO,
                param_file_name))
    else:
        param_dir = LaunchConfiguration(
            'params_file',
            default=os.path.join(
                get_package_share_directory('turtlebot3_navigation2'),
                'param',
                param_file_name))

    nav2_launch_file_dir = os.path.join(get_package_share_directory('nav2_bringup'), 'launch')

    rviz_config_dir = os.path.join(
        get_package_share_directory('turtlebot3_navigation2'),
        'rviz',
        'tb3_navigation2.rviz')

    # RFID 복귀 네비게이션 파라미터
    return_x = LaunchConfiguration('return_x', default='0.0')
    return_y = LaunchConfiguration('return_y', default='0.0')
    return_z = LaunchConfiguration('return_z', default='0.0')
    return_w = LaunchConfiguration('return_w', default='1.0')
    rfid_topic = LaunchConfiguration('rfid_topic', default='/rfid/tag')
    cooldown_sec = LaunchConfiguration('cooldown_sec', default='5.0')
    max_retries = LaunchConfiguration('max_retries', default='3')
    retry_delay_sec = LaunchConfiguration('retry_delay_sec', default='1.0')

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=map_dir,
            description='Full path to map file to load'),

        DeclareLaunchArgument(
            'params_file',
            default_value=param_dir,
            description='Full path to param file to load'),

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),

        DeclareLaunchArgument(
            'start_rviz',
            default_value=start_rviz,
            description='Start RViz2 if true'),

        # RFID 복귀 네비게이션 파라미터
        DeclareLaunchArgument(
            'return_x',
            default_value=return_x,
            description='복귀 목표의 X 좌표'),

        DeclareLaunchArgument(
            'return_y',
            default_value=return_y,
            description='복귀 목표의 Y 좌표'),

        DeclareLaunchArgument(
            'return_z',
            default_value=return_z,
            description='복귀 목표의 Z 방향 (quaternion)'),

        DeclareLaunchArgument(
            'return_w',
            default_value=return_w,
            description='복귀 목표의 W 방향 (quaternion)'),

        DeclareLaunchArgument(
            'rfid_topic',
            default_value=rfid_topic,
            description='RFID 태그 토픽 이름'),

        DeclareLaunchArgument(
            'cooldown_sec',
            default_value=cooldown_sec,
            description='RFID 태그 감지 후 쿨다운 시간 (초)'),

        DeclareLaunchArgument(
            'max_retries',
            default_value=max_retries,
            description='네비게이션 실패 시 최대 재시도 횟수'),

        DeclareLaunchArgument(
            'retry_delay_sec',
            default_value=retry_delay_sec,
            description='재시도 간 딜레이 시간 (초)'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([nav2_launch_file_dir, '/bringup_launch.py']),
            launch_arguments={
                'map': map_dir,
                'use_sim_time': use_sim_time,
                'params_file': param_dir}.items(),
        ),

        # RViz 노드는 필요할 때만 생성되도록 OpaqueFunction으로 지연 생성
        OpaqueFunction(function=lambda context: [
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz2',
                arguments=['-d', rviz_config_dir],
                parameters=[{'use_sim_time': use_sim_time}],
                output='screen')
        ] if str(LaunchConfiguration('start_rviz').perform(context)).lower() in ['1', 'true', 'yes', 'on'] else []),

        # RFID 복귀 네비게이션 노드
        Node(
            package='rfid_return_navigation',
            executable='rfid_return_navigation',
            name='rfid_return_navigation',
            parameters=[{
                'return_x': return_x,
                'return_y': return_y,
                'return_z': return_z,
                'return_w': return_w,
                'rfid_topic': rfid_topic,
                'frame_id': 'map',
                'cooldown_sec': cooldown_sec,
                'max_retries': max_retries,
                'retry_delay_sec': retry_delay_sec,
            }],
            output='screen'),
    ])
