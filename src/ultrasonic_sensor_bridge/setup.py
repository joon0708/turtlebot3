from setuptools import setup

package_name = 'ultrasonic_sensor_bridge'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/ultrasonic_publisher.launch.py',
            'launch/ultrasonic_with_lcd.launch.py',
            'launch/ultrasonic_safety_system.launch.py'
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your_email@example.com',
    description='Ultrasonic sensor bridge for TurtleBot3 - converts sensor data to ROS2 Range messages',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ultrasonic_publisher = ultrasonic_sensor_bridge.ultrasonic_publisher:main',
            'ultrasonic_publisher_direct = ultrasonic_sensor_bridge.ultrasonic_publisher_direct:main',
            'ultrasonic_publisher_ros = ultrasonic_sensor_bridge.ultrasonic_publisher_ros:main',
            'ultrasonic_lcd_display = ultrasonic_sensor_bridge.ultrasonic_lcd_display:main',
            'ultrasonic_to_laserscan = ultrasonic_sensor_bridge.ultrasonic_to_laserscan:main',
            'ultrasonic_safety_controller = ultrasonic_sensor_bridge.ultrasonic_safety_controller:main',
        ],
    },
)
