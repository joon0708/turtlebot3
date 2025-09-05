#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    # 환경 변수 설정
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi_4wheel')
    
    # Launch 파라미터
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    usb_port = LaunchConfiguration('usb_port', default='/dev/ttyACM0')
    
    return LaunchDescription([
        # Launch 파라미터 선언
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        
        DeclareLaunchArgument(
            'lidar_port',
            default_value='/dev/ttyUSB0',
            description='Connected USB port with LIDAR sensor'),
        
        DeclareLaunchArgument(
            'usb_port',
            default_value='/dev/ttyACM0',
            description='Connected USB port with OpenCR'),
        
        # 1. 하드웨어 브링업 (모터 + 센서 + TF)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_hardware_bringup'), 'launch', 'hardware.launch.py')]),
            launch_arguments={
                'lidar_port': lidar_port,
                'usb_port': usb_port,
                'use_sim_time': use_sim_time
            }.items(),
        ),
        
        # 2. 맵 저장 서비스 (네비게이션 중 맵 갱신)
        Node(
            package='nav2_map_server',
            executable='map_saver_server',
            name='map_saver_server',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'save_map_timeout': 5.0,
                'free_thresh_default': 0.25,
                'occupied_thresh_default': 0.65,
                'map_subscribe_transient_local': True
            }]
        ),
        
        # 3. 맵 업데이터 (자동 맵 저장)
        ExecuteProcess(
            cmd=['python3', '/root/turtlebot3/src/map_mode_manager/map_mode_manager/map_updater.py'],
            output='screen',
            env={
                'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                'PYTHONPATH': '/root/turtlebot3/src:' + os.environ.get('PYTHONPATH', ''),
                'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
                'PATH': os.environ.get('PATH', ''),
                'ROS_DOMAIN_ID': '10',
                'ROS_VERSION': '2',
                'ROS_DISTRO': 'humble',
                'ROS_LOG_DIR': '/root/.ros/log',
                'HOME': '/root'
            }
        ),
        
        # 4. Navigation2 (기존 맵 사용, AMCL 포함 - 맵 비교를 위해, TF 브로드캐스트 활성화)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_navigation2'), 'launch', 'navigation2_only.launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'map': os.path.join(
                    get_package_share_directory('turtlebot3_navigation2'), 'map', 'map.yaml'),
                'amcl_tf_broadcast': 'true'  # AMCL TF 브로드캐스트 활성화 (map->odom 발행)
            }.items(),
        ),
        
    ])
