#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
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
        
        # TurtleBot3 State Publisher (TF) - turtlebot3_bringup에서
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_bringup'), 'launch', 'turtlebot3_state_publisher.launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time
            }.items(),
            env={'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL}
        ),
        
        # LD08 LIDAR Node (LDS-02) - 직접 실행
        Node(
            package='ld08_driver',
            executable='ld08_driver',
            name='ld08_driver',
            parameters=[{
                'port': lidar_port,
                'frame_id': 'base_scan',
            }],
            output='screen',
            env={
                'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                'LD_LIBRARY_PATH': '/opt/ros/humble/lib:/root/turtlebot3/install/lib:/root/turtlebot3/install/custom_turtlebot3_msgs/lib',
                'ROS_LOG_DIR': '/root/.ros/log',
                'ROS_DOMAIN_ID': '10',
                'ROS_VERSION': '2',
                'ROS_DISTRO': 'humble'
            }),
        
        # TurtleBot3 Node (Motor Control) - 직접 실행
        Node(
            package='turtlebot3_node',
            executable='turtlebot3_ros',
            name='turtlebot3_node',
            output='screen',
            parameters=[
                {'use_sim_time': use_sim_time},
                os.path.join(
                    get_package_share_directory('turtlebot3_bringup'),
                    'param', 'humble', 'waffle_pi_4wheel.yaml')
            ],
            arguments=['-i', usb_port],
            env={
                'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                'LD_LIBRARY_PATH': '/opt/ros/humble/lib:/root/turtlebot3/install/lib:/root/turtlebot3/install/custom_turtlebot3_msgs/lib',
                'ROS_LOG_DIR': '/root/.ros/log',
                'ROS_DOMAIN_ID': '10',
                'ROS_VERSION': '2',
                'ROS_DISTRO': 'humble'
            }),
    ])
