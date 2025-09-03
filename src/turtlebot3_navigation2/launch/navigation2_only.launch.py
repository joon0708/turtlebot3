#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # 환경 변수 설정
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi_4wheel')
    
    # Launch 파라미터
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    return LaunchDescription([
        # Launch 파라미터 선언
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        
        # Navigation2 - 하드웨어 제외
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('nav2_bringup'), 'launch', 'bringup_launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'map': os.path.join(
                    get_package_share_directory('turtlebot3_navigation2'),
                    'map', 'map.yaml'),
                'params_file': os.path.join(
                    get_package_share_directory('turtlebot3_navigation2'),
                    'param', 'humble', TURTLEBOT3_MODEL + '.yaml')
            }.items(),
        ),
    ])