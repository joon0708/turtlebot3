cmake_minimum_required(VERSION 3.8)
project(turtlebot3_msgs)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(actionlib_msgs REQUIRED)

rosidl_generate_interfaces(turtlebot3_msgs
  "msg/SensorState.msg"
  "msg/Sound.msg"
  "msg/VersionInfo.msg"
  "srv/Sound.srv"
  "srv/CheckStatus.srv"
  DEPENDENCIES std_msgs sensor_msgs geometry_msgs actionlib_msgs
)

ament_package()
