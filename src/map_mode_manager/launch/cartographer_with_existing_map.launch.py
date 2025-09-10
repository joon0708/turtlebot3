#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """
    기존 맵에서 카토그래퍼를 이어서 실행하는 launch 파일
    """
    
    # 환경 변수 설정
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi_4wheel')
    
    # Launch arguments
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )
    
    declare_map_file_cmd = DeclareLaunchArgument(
        'map_file',
        default_value=os.path.join(
            get_package_share_directory('turtlebot3_navigation2'),
            'map', 'map.yaml'
        ),
        description='Full path to map yaml file to load'
    )
    
    declare_cartographer_config_cmd = DeclareLaunchArgument(
        'cartographer_config',
        default_value='turtlebot3_lds_2d_localization.lua',
        description='Cartographer configuration file'
    )
    
    declare_load_existing_map_cmd = DeclareLaunchArgument(
        'load_existing_map',
        default_value='true',
        description='Load existing map for cartographer'
    )
    
    # Get the launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time')
    map_file = LaunchConfiguration('map_file')
    cartographer_config = LaunchConfiguration('cartographer_config')
    load_existing_map = LaunchConfiguration('load_existing_map')
    
    # Cartographer Map Loader (기존 맵 로더) - ExecuteProcess로 실행
    map_loader_cmd = ExecuteProcess(
        cmd=['python3', os.path.join(
            get_package_share_directory('map_mode_manager'),
            '..', '..', 'lib', 'python3.10', 'site-packages', 'map_mode_manager', 'cartographer_map_loader.py'
        )],
        output='screen',
        env={
            'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
            'ROS_DOMAIN_ID': '10',
            'ROS_VERSION': '2',
            'ROS_DISTRO': 'humble',
            'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
            'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
            'PATH': os.environ.get('PATH', ''),
            'HOME': os.environ.get('HOME', '/root'),
            'USER': os.environ.get('USER', 'root'),
        }
    )
    
    # Cartographer Node (로컬라이제이션 모드)
    cartographer_node_cmd = Node(
        package='cartographer_ros',
        executable='cartographer_node',
        name='cartographer_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=[
            '-configuration_directory', os.path.join(
                get_package_share_directory('turtlebot3_cartographer'), 'config'),
            '-configuration_basename', cartographer_config
        ],
        env={
            'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
            'ROS_DOMAIN_ID': '10',
            'ROS_LOG_DIR': '/root/.ros/log',
            'LD_LIBRARY_PATH': '/opt/ros/humble/lib:/root/turtlebot3/install/custom_turtlebot3_msgs/lib'
        }
    )
    
    # Cartographer Occupancy Grid Node
    cartographer_occupancy_grid_cmd = Node(
        package='cartographer_ros',
        executable='cartographer_occupancy_grid_node',
        name='cartographer_occupancy_grid_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=['-resolution', '0.05', '-publish_period_sec', '1.0']
    )
    
    # Map Comparator (맵 비교) - ExecuteProcess로 실행
    map_comparator_cmd = ExecuteProcess(
        cmd=['python3', os.path.join(
            get_package_share_directory('map_mode_manager'),
            '..', '..', 'lib', 'python3.10', 'site-packages', 'map_mode_manager', 'map_comparator.py'
        )],
        output='screen',
        env={
            'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
            'ROS_DOMAIN_ID': '10',
            'ROS_VERSION': '2',
            'ROS_DISTRO': 'humble',
            'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
            'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
            'PATH': os.environ.get('PATH', ''),
            'HOME': os.environ.get('HOME', '/root'),
            'USER': os.environ.get('USER', 'root'),
        }
    )
    
    # Map Fusion Node (맵 융합) - ExecuteProcess로 실행
    map_fusion_cmd = ExecuteProcess(
        cmd=['python3', os.path.join(
            get_package_share_directory('map_mode_manager'),
            '..', '..', 'lib', 'python3.10', 'site-packages', 'map_mode_manager', 'map_fusion_node.py'
        )],
        output='screen',
        env={
            'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
            'ROS_DOMAIN_ID': '10',
            'ROS_VERSION': '2',
            'ROS_DISTRO': 'humble',
            'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
            'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
            'PATH': os.environ.get('PATH', ''),
            'HOME': os.environ.get('HOME', '/root'),
            'USER': os.environ.get('USER', 'root'),
        }
    )
    
    # Incremental Map Updater (점진적 맵 업데이터) - ExecuteProcess로 실행
    incremental_map_updater_cmd = ExecuteProcess(
        cmd=['python3', os.path.join(
            get_package_share_directory('map_mode_manager'),
            '..', '..', 'lib', 'python3.10', 'site-packages', 'map_mode_manager', 'incremental_map_updater.py'
        )],
        output='screen',
        env={
            'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
            'ROS_DOMAIN_ID': '10',
            'ROS_VERSION': '2',
            'ROS_DISTRO': 'humble',
            'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
            'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
            'PATH': os.environ.get('PATH', ''),
            'HOME': os.environ.get('HOME', '/root'),
            'USER': os.environ.get('USER', 'root'),
        }
    )
    
    # Navigation Map Updater (네비게이션 맵 업데이터) - ExecuteProcess로 실행
    navigation_map_updater_cmd = ExecuteProcess(
        cmd=['python3', os.path.join(
            get_package_share_directory('map_mode_manager'),
            '..', '..', 'lib', 'python3.10', 'site-packages', 'map_mode_manager', 'navigation_map_updater.py'
        )],
        output='screen',
        env={
            'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
            'ROS_DOMAIN_ID': '10',
            'ROS_VERSION': '2',
            'ROS_DISTRO': 'humble',
            'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
            'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
            'PATH': os.environ.get('PATH', ''),
            'HOME': os.environ.get('HOME', '/root'),
            'USER': os.environ.get('USER', 'root'),
        }
    )
    
    # Create the launch description and populate
    ld = LaunchDescription()
    
    # Declare the launch options
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_map_file_cmd)
    ld.add_action(declare_cartographer_config_cmd)
    ld.add_action(declare_load_existing_map_cmd)
    
    # Add the commands to the launch description
    ld.add_action(map_loader_cmd)
    ld.add_action(cartographer_node_cmd)
    ld.add_action(cartographer_occupancy_grid_cmd)
    ld.add_action(map_comparator_cmd)
    ld.add_action(map_fusion_cmd)
    ld.add_action(incremental_map_updater_cmd)
    ld.add_action(navigation_map_updater_cmd)
    
    return ld
