from setuptools import setup, find_packages
import glob
import os

package_name = 'map_mode_manager'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob.glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob.glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='TurtleBot3 User',
    maintainer_email='user@example.com',
    description='Adaptive SLAM/Localization mode switching system for TurtleBot3',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'map_topic_relay = map_mode_manager.map_topic_relay:main',
        ],
    },
)
