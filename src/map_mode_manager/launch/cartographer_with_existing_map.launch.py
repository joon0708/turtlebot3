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
    
    # Cartographer Map Loader (기존 맵 로더)
    map_loader_cmd = Node(
        package='map_mode_manager',
        executable='cartographer_map_loader.py',
        name='cartographer_map_loader',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'map_file_path': map_file,
            'load_existing_map': load_existing_map,
            'publish_loaded_map': True,
            'update_interval': 1.0
        }]
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
    
    # Map Comparator (맵 비교)
    map_comparator_cmd = Node(
        package='map_mode_manager',
        executable='map_comparator.py',
        name='map_comparator',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'scan_sampling_ratio': 0.1,
            'map_resolution': 0.05,
            'comparison_area_size': 5.0,
            'min_scan_points': 10,
            'max_scan_range': 3.5
        }]
    )
    
    # Map Fusion Node (맵 융합)
    map_fusion_cmd = Node(
        package='map_mode_manager',
        executable='map_fusion_node.py',
        name='map_fusion_node',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'change_threshold': 0.3,
            'fusion_confidence': 0.8,
            'update_interval': 2.0,
            'min_change_area': 50,
            'enable_incremental_update': True
        }]
    )
    
    # Incremental Map Updater (점진적 맵 업데이터)
    incremental_map_updater_cmd = Node(
        package='map_mode_manager',
        executable='incremental_map_updater.py',
        name='incremental_map_updater',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'base_map_path': os.path.join(
                get_package_share_directory('turtlebot3_navigation2'),
                'map'
            ),
            'backup_enabled': True,
            'max_backups': 10,
            'update_confidence_threshold': 0.8,
            'min_update_interval': 30.0,
            'auto_update_enabled': True
        }]
    )
    
    # Navigation Map Updater (네비게이션 맵 업데이터)
    navigation_map_updater_cmd = Node(
        package='map_mode_manager',
        executable='navigation_map_updater.py',
        name='navigation_map_updater',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'update_interval': 5.0,
            'min_movement_distance': 1.0,
            'exploration_threshold': 0.3,
            'auto_update_enabled': True,
            'update_during_navigation': True,
            'map_confidence_threshold': 0.7
        }]
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
