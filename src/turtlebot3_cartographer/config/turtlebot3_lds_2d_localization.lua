-- Copyright 2016 The Cartographer Authors
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--      http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- /* Author: Darby Lim */
-- /* Modified for Localization Mode - Map Preservation */

include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "imu_link",
  published_frame = "odom",
  odom_frame = "odom",
  provide_odom_frame = false,
  publish_frame_projected_to_2d = true,
  use_odometry = true,
  use_nav_sat = false,
  use_landmarks = false,
  num_laser_scans = 1,
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,
  lookup_transform_timeout_sec = 0.2,
  
  -- 맵 보존을 위한 설정
  submap_publish_period_sec = 2.0,        -- 맵 갱신 주기 증가 (0.3 → 2.0)
  pose_publish_period_sec = 0.1,          -- 포즈 발행 주기 증가 (5e-3 → 0.1)
  trajectory_publish_period_sec = 0.5,    -- 궤적 발행 주기 증가 (30e-3 → 0.5)
  
  rangefinder_sampling_ratio = 0.5,       -- 스캔 데이터 샘플링 비율 감소 (1.0 → 0.5)
  odometry_sampling_ratio = 1.,
  fixed_frame_pose_sampling_ratio = 1.,
  imu_sampling_ratio = 1.,
  landmarks_sampling_ratio = 1.,
}

MAP_BUILDER.use_trajectory_builder_2d = true

TRAJECTORY_BUILDER_2D.min_range = 0.12
TRAJECTORY_BUILDER_2D.max_range = 3.5
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 3.
TRAJECTORY_BUILDER_2D.use_imu_data = false

-- Localization 모드에서는 실시간 스캔 매칭 비활성화하여 기존 맵 보존
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = false

-- 모션 필터링 강화하여 불필요한 맵 업데이트 방지
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_radians = math.rad(0.5)  -- 0.1 → 0.5
TRAJECTORY_BUILDER_2D.motion_filter.max_distance_meters = 0.1          -- 추가: 거리 기반 필터링

-- 포즈 그래프 최적화 빈도 감소
POSE_GRAPH.constraint_builder.min_score = 0.75        -- 0.65 → 0.75 (더 엄격한 매칭)
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.8  -- 0.7 → 0.8

-- 포즈 그래프 최적화 빈도 감소하여 맵 안정성 향상
POSE_GRAPH.optimize_every_n_nodes = 20               -- 추가: 20개 노드마다 최적화

return options
