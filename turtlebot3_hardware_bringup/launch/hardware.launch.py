#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # 환경 변수 설정 - 4바퀴 시스템용
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi_4wheel')
    
    # Launch 파라미터
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    usb_port = LaunchConfiguration('usb_port', default='/dev/ttyACM0')
    namespace = LaunchConfiguration('namespace', default='')
    use_4wheel = LaunchConfiguration('use_4wheel', default='true')
    
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
            'namespace',
            default_value='',
            description='Namespace for nodes'),

        DeclareLaunchArgument(
            'use_4wheel',
            default_value='true',
            description='Use 4-wheel configuration if true'),
        
        # TurtleBot3 기본 브링업 (URDF, 파라미터, 기본 노드들)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_bringup'), 'launch', 'turtlebot3_state_publisher.launch.py')]),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
        ),
        
        # LD08 LIDAR Node (LDS-02) - 포트만 설정
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_bringup'), 'launch', 'ld08_driver.launch.py')]),
            launch_arguments={
                'port': lidar_port,
                'frame_id': 'base_scan'
            }.items(),
        ),
        
        # TurtleBot3 Node (Motor Control) - 포트만 설정
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_bringup'), 'launch', 'turtlebot3_node.launch.py')]),
            launch_arguments={
                'usb_port': usb_port,
                'use_sim_time': use_sim_time
            }.items(),
        ),
    ])
