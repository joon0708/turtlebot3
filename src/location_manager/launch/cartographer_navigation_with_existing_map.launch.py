#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # 환경 변수 설정
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi_4wheel')
    
    # Launch 파라미터
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    usb_port = LaunchConfiguration('usb_port', default='/dev/ttyACM1')
    
    # 기존 맵 경로
    existing_map_path = LaunchConfiguration('existing_map_path', 
        default='/root/turtlebot3/install/turtlebot3_navigation2/share/turtlebot3_navigation2/map/map.yaml')
    
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
            default_value='/dev/ttyACM1',
            description='Connected USB port with OpenCR'),
        
        DeclareLaunchArgument(
            'existing_map_path',
            default_value='/root/turtlebot3/install/turtlebot3_navigation2/share/turtlebot3_navigation2/map/map.yaml',
            description='Path to existing map file'),
        
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
        
        # 2. 기존 맵 로드 (Map Server)
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'yaml_filename': existing_map_path
            }]),
        
        # 3. Cartographer (SLAM) - 기존 맵과 함께 동작
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_cartographer'), 'launch', 'cartographer_only.launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time
            }.items(),
        ),
        
        # 4. Navigation2
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_navigation2'), 'launch', 'navigation2_only.launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'map': existing_map_path
            }.items(),
        ),
        
        # 5. Location Manager
        Node(
            package='location_manager',
            executable='location_manager',
            name='location_manager',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time
            }]),
        
        # 6. 초음파 센서 브리지
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('ultrasonic_sensor_bridge'), 'launch', 'ultrasonic_sensor_bridge.launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time
            }.items(),
        ),
    ])
