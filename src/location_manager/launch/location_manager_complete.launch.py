#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition
from launch_ros.actions import Node

def generate_launch_description():
    # 환경 변수 설정
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi_4wheel')
    
    # Launch 파라미터
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    usb_port = LaunchConfiguration('usb_port', default='/dev/ttyACM0')
    external_map_path = LaunchConfiguration('external_map_path', default='')
    use_external_map = LaunchConfiguration('use_external_map', default='false')
    
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
        
        DeclareLaunchArgument(
            'external_map_path',
            default_value=os.path.join(get_package_share_directory('turtlebot3_navigation2'), 'map'),
            description='External map path (e.g., turtlebot3_navigation2/map)'),
        
        DeclareLaunchArgument(
            'use_external_map',
            default_value='true',
            description='Use external map from another package'),
        
        DeclareLaunchArgument(
            'use_location_manager',
            default_value='true',
            description='Launch location manager node'),
        
        DeclareLaunchArgument(
            'use_cartographer',
            default_value='false',
            description='Launch Cartographer SLAM system'),
        
        # 1. 하드웨어 브링업 (모터 + 센서 + TF) - 한 번만
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_hardware_bringup'), 'launch', 'hardware.launch.py')]),
            launch_arguments={
                'lidar_port': lidar_port,
                'usb_port': usb_port,
                'use_sim_time': use_sim_time
            }.items(),
        ),
        
        # 2. 적응형 Cartographer (SLAM/Localization) - map_mode_manager 사용 (선택적)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('map_mode_manager'), 'launch', 'adaptive_cartographer.launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'map_directory': os.path.join(get_package_share_directory('turtlebot3_navigation2'), 'map'),
                'enable_map_protection': 'true',
                'auto_backup_maps': 'true',
                'use_external_map': use_external_map,
                'external_map_path': external_map_path,
                'start_mode': 'slam'  # 실시간 맵 생성을 위해 SLAM 모드로 시작
            }.items(),
            condition=IfCondition(LaunchConfiguration('use_cartographer', default='false')),
        ),
        
        # 3. Navigation2 - 항상 실행 (AMCL 포함)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_navigation2'), 'launch', 'navigation2_only.launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'map': os.path.join(get_package_share_directory('turtlebot3_navigation2'), 'map', 'map.yaml'),
                'amcl_use_map_topic': 'true'  # AMCL이 맵 토픽을 사용하도록 설정
            }.items(),
        ),
        
        # 4. 위치 관리 노드
        Node(
            package='location_manager',
            executable='location_manager',
            name='location_manager',
            output='screen',
            env={
                'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                'ROS_DOMAIN_ID': '10',
                'ROS_VERSION': '2',
                'ROS_DISTRO': 'humble',
                'ROS_LOG_DIR': '/root/.ros/log'
            },
            condition=IfCondition(LaunchConfiguration('use_location_manager', default='true'))
        ),
    ])