#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='location_manager',
            executable='touch_ui.py',
            name='touch_ui',
            output='screen',
            env={
                'TB3_UI_FULLSCREEN': os.environ.get('TB3_UI_FULLSCREEN', '1'),
            }
        )
    ])


