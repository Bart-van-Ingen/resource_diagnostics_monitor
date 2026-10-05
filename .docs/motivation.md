# Motivation

Monitoring system resources is important for maintaining the health and determining performance of
robotic systems. There does not seem to be a well established solution to do this in ROS 2, with
these the current ones that can be found easily online:

- [AgoraRobotics/ros2-system-monitor](https://github.com/AgoraRobotics/ros2-system-monitor)
- [kei1107/ros2-system-monitor](https://github.com/kei1107/ros2-system-monitor)
- [ethz-asl/ros-system-monitor](https://github.com/ethz-asl/ros-system-monitor)
- [tier4/system_monitor](https://tier4.github.io/autoware.iv/tree/main/system/system_monitor/)

This project attempts to fill that gap.

## Why a metric collector

Resource monitoring is not a problem unique to robotics. The cloud native and DevOps communities
already have mature tools that do this well. These tools are called metric collectors. This
package uses one of two:

- [Telegraf](https://www.influxdata.com/time-series-platform/telegraf/)
- [collectd](https://github.com/collectd/collectd)

A metric collector reads metrics from the system with input plugins and sends them to a destination
with output plugins. In this package, the destination is a unix socket. The ROS 2 node reads the
socket and publishes each metric as a ROS message.

This gives the following advantages:

- **No need to reinvent the wheel.** The collectors already read CPU, memory, disk, temperature,
  process and many other metrics. This package does not have to write and maintain that code.
- **Configuration instead of code.** The user selects what to monitor in the collector config
  file. For example, Telegraf's `inputs.cpu` plugin has a `percpu` option. Set it to `false` and the
  per core topics are gone. No rebuild of the ROS 2 package is necessary.
- **Advanced features.** Telegraf has processors and aggregators to clean up, tag and combine
  metrics before they reach ROS 2.
- **Collector is replaceable.** The ROS 2 node only reads the socket. It does not care which
  collector writes to it.
- **Remote monitoring.** Telegraf can also send the same metrics over the OTLP protocol, which is a
  common standard for telemetry data. This can connect to any
  [OpenTelemetry collector](https://opentelemetry.io/docs/collector/distributions/), which can then
  pass it on to the remote monitoring environment of your choice.


## Why diagnostics is not built into the monitor

The resource monitor publishes its own message types, not `diagnostic_msgs`. A separate, optional
node (`resource_diagnostics_updater_py/cpp`) turns the resource topics into diagnostics. There are
two reasons for this split.

### Diagnostics has a specific purpose

The design is based on the ROSCon 2024 talk
[How is my robot? - On the state of ROS Diagnostics](https://roscon.ros.org/2024/talks/How_is_my_robot_-_On_the_state_of_ROS_Diagnostics.pdf)
by Christian Henkel. It gives these points about diagnostics:

- Main purpose: observe the current state of the robot.
- In general, diagnostics are not meant to be used functionally.
- Diagnostics are meant as a communication method from robot to human.

Resource metrics can also be used functionally. For example, a node can change its behaviour when
the CPU load is high. The resource monitor does not assume how the user uses the data. Diagnostics
is one possible use, not the only one.

### Diagnostics needs choices that depend on the use case

[REP 107](https://reps.openrobotics.org/rep-0107/) describes the ROS diagnostics system. To follow
it, the monitor must publish on `/diagnostics` with the `diagnostic_msgs/DiagnosticArray` type. Each
status must also have a level (OK, WARN, ERROR). The correct thresholds for these levels depend on
the robot and the use case. The monitor cannot know them.

The diagnostics updater node solves this. The user gives the thresholds in
`resource_diagnostics.yaml`, and only for the resources that they want in diagnostics.

### Resource cost of the topics

Each topic in the system uses some resources itself. This is much more true for ROS 2 than for
ROS 1. A monitor that publishes many topics therefore adds to the load that it measures.

The C++ version partly solves this. The bringup launch file loads the monitor and the diagnostics
updater into one process with intra-process communication on. If no other node subscribes to a
resource topic, its messages do not go through the middleware at all. See
[Intra-Process Communication](learnings/intra_process_communication.md).



## Why not standard sensor messages

Standard messages such as `sensor_msgs/Temperature` were also considered. They lose data. For
example, a temperature metric from Telegraf has these fields:

```yaml
fields:
  - name: temp_crit
    value: 125.0
  - name: temp_input
    value: 56.0
```

`sensor_msgs/Temperature` has no field for `temp_crit`. The custom messages in
`resource_monitor_interfaces` keep all fields.
