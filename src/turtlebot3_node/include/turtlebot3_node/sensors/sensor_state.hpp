// Copyright 2019 ROBOTIS CO., LTD.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Author: Darby Lim

#ifndef TURTLEBOT3_NODE__SENSORS__SENSOR_STATE_HPP_
#define TURTLEBOT3_NODE__SENSORS__SENSOR_STATE_HPP_

#include <custom_turtlebot3_msgs/msg/sensor_state.hpp>

#include <memory>
#include <string>

#include "turtlebot3_node/sensors/sensors.hpp"

namespace robotis
{
namespace turtlebot3
{
namespace sensors
{
class SensorState : public Sensors
{
public:
  explicit SensorState(
    std::shared_ptr<rclcpp::Node> & nh,
    const std::string & topic_name = "sensor_state",
    const uint8_t & bumper_forward = 0,
    const uint8_t & bumper_backward = 0,
    const uint8_t & illumination = 0,
    const uint8_t & cliff = 0,
    const uint8_t & sonar = 0,
    const uint8_t & ultrasonic_left = 0,
    const uint8_t & ultrasonic_front = 0,
    const uint8_t & ultrasonic_right = 0);

  void publish(
    const rclcpp::Time & now,
    std::shared_ptr<DynamixelSDKWrapper> & dxl_sdk_wrapper) override;

private:
  rclcpp::Publisher<custom_turtlebot3_msgs::msg::SensorState>::SharedPtr pub_;

  uint8_t bumper_forward_;
  uint8_t bumper_backward_;
  uint8_t illumination_;
  uint8_t cliff_;
  uint8_t sonar_;
  uint8_t ultrasonic_left_;
  uint8_t ultrasonic_front_;
  uint8_t ultrasonic_right_;
  
  // 50Hz 데이터를 20개씩 버퍼링해서 처리
  static constexpr size_t BUFFER_SIZE = 20;
  std::vector<float> left_buffer_;
  std::vector<float> front_buffer_;
  std::vector<float> right_buffer_;
  size_t buffer_index_;
  bool buffer_full_;
  
  // 이전 초음파 센서 값 저장 (nan 필터링용)
  float prev_ultrasonic_left_;
  float prev_ultrasonic_front_;
  float prev_ultrasonic_right_;
};
}  // namespace sensors
}  // namespace turtlebot3
}  // namespace robotis
#endif  // TURTLEBOT3_NODE__SENSORS__SENSOR_STATE_HPP_
