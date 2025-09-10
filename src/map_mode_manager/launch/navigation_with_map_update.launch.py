#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """
    네비게이션과 실시간 맵 갱신을 통합한 launch 파일
    """
    
    # 환경 변수 설정
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi')
    
    # Launch arguments
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )
    
    declare_map_file_cmd = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(
            get_package_share_directory('turtlebot3_navigation2'),
            'map', 'map.yaml'
        ),
        description='Full path to map yaml file to load'
    )
    
    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(
            get_package_share_directory('turtlebot3_navigation2'),
            'param', f'{TURTLEBOT3_MODEL}.yaml'
        ),
        description='Full path to the ROS2 parameters file to use for all launched nodes'
    )
    
    declare_bt_loop_duration_cmd = DeclareLaunchArgument(
        'bt_loop_duration',
        default_value='10',
        description='Behavior tree loop duration'
    )
    
    declare_enable_slam_cmd = DeclareLaunchArgument(
        'enable_slam',
        default_value='false',
        description='Enable SLAM during navigation'
    )
    
    declare_enable_map_update_cmd = DeclareLaunchArgument(
        'enable_map_update',
        default_value='true',
        description='Enable real-time map updating during navigation'
    )
    
    declare_update_interval_cmd = DeclareLaunchArgument(
        'update_interval',
        default_value='5.0',
        description='Map update interval in seconds'
    )
    
    # Get the launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml_file = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    bt_loop_duration = LaunchConfiguration('bt_loop_duration')
    enable_slam = LaunchConfiguration('enable_slam')
    enable_map_update = LaunchConfiguration('enable_map_update')
    update_interval = LaunchConfiguration('update_interval')
    
    # Map server
    map_server_cmd = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'yaml_filename': map_yaml_file
        }]
    )
    
    # AMCL
    amcl_cmd = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[params_file]
    )
    
    # Navigation2
    navigation2_cmd = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'bt_loop_duration': bt_loop_duration,
            'default_server_timeout': 20.0,
            'enable_groot_monitoring': True,
            'default_nav_to_pose_bt_xml': os.path.join(
                get_package_share_directory('nav2_bt_navigator'),
                'behavior_trees', 'navigate_to_pose_w_replanning_and_recovery.xml'
            )
        }]
    )
    
    # Navigation2 Planner
    planner_cmd = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[params_file]
    )
    
    # Navigation2 Controller
    controller_cmd = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[params_file]
    )
    
    # Navigation2 Recovery
    recovery_cmd = Node(
        package='nav2_recoveries',
        executable='recoveries_server',
        name='recoveries_server',
        output='screen',
        parameters=[params_file]
    )
    
    # Navigation2 Waypoint Follower
    waypoint_follower_cmd = Node(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        name='waypoint_follower',
        output='screen',
        parameters=[params_file]
    )
    
    # Navigation2 Velocity Smoother
    velocity_smoother_cmd = Node(
        package='nav2_velocity_smoother',
        executable='velocity_smoother',
        name='velocity_smoother',
        output='screen',
        parameters=[params_file]
    )
    
    # Lifecycle Manager
    lifecycle_manager_cmd = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'autostart': True,
            'node_names': [
                'map_server',
                'amcl',
                'planner_server',
                'controller_server',
                'recoveries_server',
                'bt_navigator',
                'waypoint_follower',
                'velocity_smoother'
            ]
        }]
    )
    
    # SLAM (조건부)
    slam_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('turtlebot3_cartographer'),
                'launch', 'cartographer.launch.py'
            )
        ]),
        condition=IfCondition(enable_slam),
        launch_arguments={
            'use_sim_time': use_sim_time
        }.items()
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
    
    # Map Similarity Checker (맵 유사도 체커)
    map_similarity_checker_cmd = Node(
        package='map_mode_manager',
        executable='map_similarity_checker.py',
        name='map_similarity_checker',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'similarity_threshold': 0.8,
            'check_interval': 5.0,
            'mode_switch_delay': 2.0,
            'min_samples_for_decision': 3,
            'similarity_window_size': 10,
            'stability_threshold': 0.1
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
    
    # Navigation Map Updater (네비게이션 맵 업데이터) - 조건부
    navigation_map_updater_cmd = Node(
        package='map_mode_manager',
        executable='navigation_map_updater.py',
        name='navigation_map_updater',
        output='screen',
        condition=IfCondition(enable_map_update),
        parameters=[{
            'use_sim_time': use_sim_time,
            'update_interval': update_interval,
            'min_movement_distance': 1.0,
            'exploration_threshold': 0.3,
            'auto_update_enabled': True,
            'update_during_navigation': True,
            'map_confidence_threshold': 0.7
        }]
    )
    
    # Map Updater (기본 맵 업데이터)
    map_updater_cmd = Node(
        package='map_mode_manager',
        executable='map_updater.py',
        name='map_updater',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )
    
    # Create the launch description and populate
    ld = LaunchDescription()
    
    # Declare the launch options
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_map_file_cmd)
    ld.add_action(declare_params_file_cmd)
    ld.add_action(declare_bt_loop_duration_cmd)
    ld.add_action(declare_enable_slam_cmd)
    ld.add_action(declare_enable_map_update_cmd)
    ld.add_action(declare_update_interval_cmd)
    
    # Add the commands to the launch description
    ld.add_action(map_server_cmd)
    ld.add_action(amcl_cmd)
    ld.add_action(navigation2_cmd)
    ld.add_action(planner_cmd)
    ld.add_action(controller_cmd)
    ld.add_action(recovery_cmd)
    ld.add_action(waypoint_follower_cmd)
    ld.add_action(velocity_smoother_cmd)
    ld.add_action(lifecycle_manager_cmd)
    
    # SLAM (조건부)
    ld.add_action(slam_cmd)
    
    # Map management nodes
    ld.add_action(map_comparator_cmd)
    ld.add_action(map_similarity_checker_cmd)
    ld.add_action(incremental_map_updater_cmd)
    ld.add_action(navigation_map_updater_cmd)
    ld.add_action(map_updater_cmd)
    
    return ld
