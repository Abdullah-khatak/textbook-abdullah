# Navigation with Nav2

## Learning Objectives

By the end of this chapter, you will be able to:

- Understand the Nav2 navigation stack architecture
- Configure Nav2 for humanoid robots
- Implement path planning algorithms
- Use costmaps for obstacle representation
- Create behavior trees for complex navigation
- Tune navigation parameters for optimal performance
- Handle dynamic obstacles and recovery behaviors
- Deploy autonomous navigation on real robots

## What is Nav2?

**Nav2 (Navigation2)** is the ROS 2 navigation framework. It enables autonomous mobile robots to:
- Plan collision-free paths
- Follow paths while avoiding obstacles
- Recover from failures
- Navigate in dynamic environments

Nav2 is the successor to the ROS 1 navigation stack, rebuilt for ROS 2 with improved modularity, performance, and flexibility.

## Nav2 Architecture

Nav2 consists of several interconnected servers and plugins:

### Core Components
```
Nav2 Architecture
├── BT Navigator Server (Behavior Trees)
├── Planner Server (Global path planning)
├── Controller Server (Local path following)
├── Smoother Server (Path smoothing)
├── Recovery Server (Recovery behaviors)
├── Waypoint Follower (Multi-waypoint navigation)
└── Lifecycle Manager (Node management)
```

### Data Flow
```
Goal → BT Navigator → Planner → Path → Controller → Velocity Commands
                          ↓
                      Costmaps (Global & Local)
                          ↑
                    Sensor Data (LiDAR, Camera)
```

## Installing Nav2

### Installation
```bash
# Install Nav2 packages
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup

# Install SLAM Toolbox (for mapping)
sudo apt install ros-humble-slam-toolbox

# Install RViz plugins
sudo apt install ros-humble-rviz2
```

### Verify Installation
```bash
ros2 pkg list | grep nav2
```

You should see packages like:
- `nav2_bt_navigator`
- `nav2_planner`
- `nav2_controller`
- `nav2_costmap_2d`

## Prerequisites for Navigation

Nav2 requires:

1. **Robot with differential drive or omnidirectional base**
2. **Localization**: AMCL (for known maps) or SLAM (for unknown maps)
3. **Sensor data**: LiDAR or depth camera
4. **TF tree**: Properly configured coordinate frames
5. **Map** (for map-based navigation)

### TF Tree Structure
```
map → odom → base_link → sensors (lidar_link, camera_link, etc.)
```

**Key frames**:
- `map`: Fixed world frame
- `odom`: Odometry frame (drifts over time)
- `base_link`: Robot's base

## Creating a Map with SLAM Toolbox

Before navigation, create a map:

### Launch SLAM Toolbox
```bash
# Start robot (simulation or real)
ros2 launch my_robot robot.launch.py

# Start SLAM
ros2 launch slam_toolbox online_async_launch.py
```

### Drive Robot to Map Environment
```bash
# Teleoperate robot to explore
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Use keyboard to drive around and build map.

### Save Map
```bash
ros2 run nav2_map_server map_saver_cli -f my_map
```

This creates:
- `my_map.yaml`: Map metadata
- `my_map.pgm`: Occupancy grid image

## Configuring Nav2

Nav2 configuration is done via YAML files.

### Basic Nav2 Configuration

Create `nav2_params.yaml`:
```yaml
bt_navigator:
  ros__parameters:
    use_sim_time: True
    global_frame: map
    robot_base_frame: base_link
    odom_topic: /odom
    bt_loop_duration: 10
    default_server_timeout: 20
    enable_groot_monitoring: True
    groot_zmq_publisher_port: 1666
    groot_zmq_server_port: 1667
    default_nav_to_pose_bt_xml: ""
    default_nav_through_poses_bt_xml: ""

planner_server:
  ros__parameters:
    expected_planner_frequency: 20.0
    use_sim_time: True
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_navfn_planner/NavfnPlanner"
      tolerance: 0.5
      use_astar: false
      allow_unknown: true

controller_server:
  ros__parameters:
    use_sim_time: True
    controller_frequency: 20.0
    min_x_velocity_threshold: 0.001
    min_y_velocity_threshold: 0.5
    min_theta_velocity_threshold: 0.001
    failure_tolerance: 0.3
    progress_checker_plugin: "progress_checker"
    goal_checker_plugins: ["general_goal_checker"]
    controller_plugins: ["FollowPath"]
    
    progress_checker:
      plugin: "nav2_controller::SimpleProgressChecker"
      required_movement_radius: 0.5
      movement_time_allowance: 10.0
    
    general_goal_checker:
      stateful: True
      plugin: "nav2_controller::SimpleGoalChecker"
      xy_goal_tolerance: 0.25
      yaw_goal_tolerance: 0.25
    
    FollowPath:
      plugin: "dwb_core::DWBLocalPlanner"
      debug_trajectory_details: True
      min_vel_x: 0.0
      min_vel_y: 0.0
      max_vel_x: 0.26
      max_vel_y: 0.0
      max_vel_theta: 1.0
      min_speed_xy: 0.0
      max_speed_xy: 0.26
      min_speed_theta: 0.0
      acc_lim_x: 2.5
      acc_lim_y: 0.0
      acc_lim_theta: 3.2
      decel_lim_x: -2.5
      decel_lim_y: 0.0
      decel_lim_theta: -3.2
      vx_samples: 20
      vy_samples: 5
      vtheta_samples: 20
      sim_time: 1.7
      linear_granularity: 0.05
      angular_granularity: 0.025
      transform_tolerance: 0.2
      xy_goal_tolerance: 0.25
      trans_stopped_velocity: 0.25
      short_circuit_trajectory_evaluation: True
      stateful: True
      critics: ["RotateToGoal", "Oscillation", "BaseObstacle", "GoalAlign", "PathAlign", "PathDist", "GoalDist"]
      
      BaseObstacle.scale: 0.02
      PathAlign.scale: 32.0
      PathAlign.forward_point_distance: 0.1
      GoalAlign.scale: 24.0
      GoalAlign.forward_point_distance: 0.1
      PathDist.scale: 32.0
      GoalDist.scale: 24.0
      RotateToGoal.scale: 32.0
      RotateToGoal.slowing_factor: 5.0
      RotateToGoal.lookahead_time: -1.0

local_costmap:
  local_costmap:
    ros__parameters:
      update_frequency: 5.0
      publish_frequency: 2.0
      global_frame: odom
      robot_base_frame: base_link
      use_sim_time: True
      rolling_window: true
      width: 3
      height: 3
      resolution: 0.05
      robot_radius: 0.22
      plugins: ["voxel_layer", "inflation_layer"]
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.55
      voxel_layer:
        plugin: "nav2_costmap_2d::VoxelLayer"
        enabled: True
        publish_voxel_map: True
        origin_z: 0.0
        z_resolution: 0.05
        z_voxels: 16
        max_obstacle_height: 2.0
        mark_threshold: 0
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: True
          marking: True
          data_type: "LaserScan"
          raytrace_max_range: 3.0
          raytrace_min_range: 0.0
          obstacle_max_range: 2.5
          obstacle_min_range: 0.0
      static_layer:
        plugin: "nav2_costmap_2d::StaticLayer"
        map_subscribe_transient_local: True
      always_send_full_costmap: True

global_costmap:
  global_costmap:
    ros__parameters:
      update_frequency: 1.0
      publish_frequency: 1.0
      global_frame: map
      robot_base_frame: base_link
      use_sim_time: True
      robot_radius: 0.22
      resolution: 0.05
      track_unknown_space: true
      plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        enabled: True
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: True
          marking: True
          data_type: "LaserScan"
          raytrace_max_range: 3.0
          raytrace_min_range: 0.0
          obstacle_max_range: 2.5
          obstacle_min_range: 0.0
      static_layer:
        plugin: "nav2_costmap_2d::StaticLayer"
        map_subscribe_transient_local: True
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.55
      always_send_full_costmap: True
```

## Launching Nav2

### Launch File

Create `nav2_launch.py`:
```python
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    
    return LaunchDescription([
        # Map server
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'yaml_filename': '/path/to/my_map.yaml'
            }]
        ),
        
        # AMCL (localization)
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=['/path/to/nav2_params.yaml']
        ),
        
        # Lifecycle manager
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'autostart': True,
                'node_names': ['map_server', 'amcl']
            }]
        ),
        
        # Nav2
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
            ),
            launch_arguments={
                'use_sim_time': 'True',
                'params_file': '/path/to/nav2_params.yaml'
            }.items()
        ),
    ])
```

### Run Navigation
```bash
# Terminal 1: Launch robot and sensors
ros2 launch my_robot robot.launch.py

# Terminal 2: Launch Nav2
ros2 launch my_robot nav2_launch.py

# Terminal 3: Launch RViz
rviz2 -d $(ros2 pkg prefix nav2_bringup)/share/nav2_bringup/rviz/nav2_default_view.rviz
```

## Setting Navigation Goals

### Using RViz

1. Click **2D Pose Estimate** button
2. Click on map where robot is, drag to set orientation
3. Click **2D Nav Goal** button
4. Click destination, drag to set goal orientation
5. Robot plans and navigates!

### Programmatically
```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient

class NavigationClient(Node):
    def __init__(self):
        super().__init__('navigation_client')
        
        self._action_client = ActionClient(
            self,
            NavigateToPose,
            'navigate_to_pose'
        )
        
    def send_goal(self, x, y, theta):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0
        
        # Convert theta to quaternion
        import math
        goal_msg.pose.pose.orientation.z = math.sin(theta / 2)
        goal_msg.pose.pose.orientation.w = math.cos(theta / 2)
        
        self._action_client.wait_for_server()
        
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        
        self._send_goal_future.add_done_callback(self.goal_response_callback)
        
    def goal_response_callback(self, future):
        goal_handle = future.result()
        
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            return
        
        self.get_logger().info('Goal accepted')
        
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)
        
    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info('Navigation completed!')
        
    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(
            f'Distance remaining: {feedback.distance_remaining:.2f}m'
        )

def main():
    rclpy.init()
    
    nav_client = NavigationClient()
    
    # Send goal: x=2.0, y=1.0, theta=0.0 (facing forward)
    nav_client.send_goal(2.0, 1.0, 0.0)
    
    rclpy.spin(nav_client)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Understanding Costmaps

**Costmaps** represent the environment as a grid where each cell has a cost (0-255):
- **0 (white)**: Free space
- **1-252 (gray)**: Inflation zone (higher cost near obstacles)
- **253-254**: Inscribed (robot barely fits)
- **255 (black)**: Lethal (obstacle)

### Costmap Layers

1. **Static Layer**: From map file (walls, furniture)
2. **Obstacle Layer**: From sensors (dynamic obstacles)
3. **Inflation Layer**: Adds safety margin around obstacles
4. **Voxel Layer**: 3D obstacle representation

### Tuning Costmaps

**Robot Radius**: Must match physical robot size
```yaml
robot_radius: 0.22  # meters
```

**Inflation Radius**: Safety margin
```yaml
inflation_radius: 0.55  # Should be > robot_radius
cost_scaling_factor: 3.0  # Higher = steeper cost gradient
```

## Path Planning Algorithms

Nav2 supports multiple global planners:

### NavFn Planner (Default)

Uses Dijkstra's algorithm:
```yaml
planner_plugins: ["GridBased"]
GridBased:
  plugin: "nav2_navfn_planner/NavfnPlanner"
  tolerance: 0.5
  use_astar: false  # Set true for A* instead of Dijkstra
```

**Pros**: Guaranteed optimal path  
**Cons**: Slower than A*

### Smac Planner (Hybrid A*)

Better for non-holonomic robots (differential drive):
```yaml
GridBased:
  plugin: "nav2_smac_planner/SmacPlannerHybrid"
  tolerance: 0.5
  motion_model_for_search: "DUBIN"  # or "REEDS_SHEPP"
  angle_quantization_bins: 72
```

**Pros**: Considers robot kinematics  
**Cons**: More computationally expensive

## Local Controllers

Controls robot to follow planned path while avoiding obstacles.

### DWB (Dynamic Window Approach)

Default controller, samples velocity space:
```yaml
FollowPath:
  plugin: "dwb_core::DWBLocalPlanner"
  max_vel_x: 0.26
  max_vel_theta: 1.0
  acc_lim_x: 2.5
  sim_time: 1.7  # Look-ahead time
```

### TEB (Timed Elastic Band)

Optimizes trajectory in space and time:
```yaml
FollowPath:
  plugin: "teb_local_planner::TebLocalPlannerROS"
  max_vel_x: 0.4
  max_vel_theta: 2.0
```

**Pros**: Smoother trajectories  
**Cons**: More CPU intensive

### Regulated Pure Pursuit

Simple and efficient for differential drive:
```yaml
FollowPath:
  plugin: "nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController"
  desired_linear_vel: 0.5
  lookahead_dist: 0.6
  min_lookahead_dist: 0.3
  max_lookahead_dist: 0.9
```

## Behavior Trees

Nav2 uses **Behavior Trees** to coordinate navigation behaviors.

### Default Navigation BT
```xml
<root>
  <BehaviorTree ID="NavigateWithReplanning">
    <PipelineSequence>
      <RateController hz="1.0">
        <RecoveryNode number_of_retries="6">
          <PipelineSequence>
            <ComputePathToPose goal="{goal}" path="{path}"/>
            <FollowPath path="{path}"/>
          </PipelineSequence>
          <SequenceStar>
            <ClearEntireCostmap service_name="global_costmap/clear_entirely_global_costmap"/>
            <ClearEntireCostmap service_name="local_costmap/clear_entirely_local_costmap"/>
            <Spin spin_dist="1.57"/>
            <Wait wait_duration="5"/>
          </SequenceStar>
        </RecoveryNode>
      </RateController>
    </PipelineSequence>
  </BehaviorTree>
</root>
```

### Custom Recovery Behaviors

Add custom behaviors when navigation fails:
- Clear costmaps
- Rotate in place
- Back up
- Wait and retry

## Handling Dynamic Obstacles

### Obstacle Layer Configuration
```yaml
obstacle_layer:
  enabled: True
  observation_sources: scan
  scan:
    topic: /scan
    clearing: True  # Remove obstacles when not detected
    marking: True   # Add new obstacles
    max_obstacle_height: 2.0
    obstacle_max_range: 2.5
    raytrace_max_range: 3.0
```

### Velocity Obstacles

For moving obstacles, use velocity costmap layer (experimental).

## Humanoid-Specific Considerations

Humanoids have unique navigation challenges:

### Balance Constraints

- Cannot stop instantly (momentum)
- Require smooth velocity changes
- Limited lateral movement

**Configuration**:
```yaml
acc_lim_x: 1.0  # Lower acceleration for stability
decel_lim_x: -1.0  # Gradual deceleration
min_speed_xy: 0.1  # Minimum speed to maintain balance
```

### Footprint

Use polygon footprint instead of circle:
```yaml
footprint: [[-0.3, -0.2], [-0.3, 0.2], [0.3, 0.2], [0.3, -0.2]]
```

### Recovery Behaviors

Humanoids cannot rotate in place easily:
- Use wider turning radius
- Plan paths with gradual turns
- Implement shuffle-turn behavior

## Performance Tuning

### Controller Frequency

Higher = smoother, but more CPU:
```yaml
controller_frequency: 20.0  # Hz (10-50 typical range)
```

### Planner Frequency

How often to replan:
```yaml
expected_planner_frequency: 1.0  # Hz (0.5-5 typical)
```

### Simulation Time

Local planner look-ahead:
```yaml
sim_time: 1.7  # seconds (1.0-3.0 typical)
```

### Samples

More samples = smoother but slower:
```yaml
vx_samples: 20  # Linear velocity samples
vtheta_samples: 20  # Angular velocity samples
```

## Key Takeaways

✅ **Nav2** provides complete autonomous navigation for ROS 2  
✅ **Costmaps** represent environment with obstacle costs  
✅ **Global planners** find optimal paths through known space  
✅ **Local controllers** follow paths while avoiding dynamic obstacles  
✅ **Behavior trees** coordinate complex navigation behaviors  
✅ **Tuning is critical** for optimal performance on specific robots

## What's Next?

Congratulations on completing Module 3! You now understand NVIDIA Isaac platform and Nav2 navigation. In Module 4, we'll integrate Language Models with robotics for natural language control.

Continue to: [Module 4: Vision-Language-Action →](/docs/module4/introduction-vla)

## Exercises

### Exercise 1: Basic Navigation
Set up Nav2 for your robot. Navigate to multiple waypoints in a known map.

### Exercise 2: Dynamic Obstacles
Test navigation with moving obstacles. Observe avoidance behaviors.

### Exercise 3: Parameter Tuning
Experiment with different controller parameters. Find optimal settings for smooth motion.

### Exercise 4: Custom Behavior Tree
Create a custom BT that visits multiple waypoints and returns home.

### Exercise 5: Humanoid Navigation
Configure Nav2 for a simulated humanoid robot. Account for balance constraints.

---

**Navigation**: [← Previous: Isaac ROS](/docs/module3/isaac-ros) | [Next: Module 4 →](/docs/module4/introduction-vla)