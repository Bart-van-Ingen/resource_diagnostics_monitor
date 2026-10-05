<p align="center">
   <img src=".docs/images/resource-monitor-lizard-logo.png" alt="Resource Monitor Lizard Logo" width="30%" />
</p>

# Resource Diagnostics Monitor

This repository provides a ROS 2-based resource monitoring solution that leverages one of two metric collectors,
[Telegraf](https://www.influxdata.com/time-series-platform/telegraf/) or
[collectd](https://github.com/collectd/collectd), to collect system metrics and publish them as ROS messages, with the possibility of also plugging into ROS2 diagnostics. It is
designed to be easily configurable and extensible, allowing users to monitor various system
resources such as CPU, memory, disk usage, and more. There are two implementations, one in Python
and one in CPP.

## Documentation

The motivation, architecture and more can be found on the accompanying pages:
<https://bart-van-ingen.github.io/resource_diagnostics_monitor/>

## Table of Contents

- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Installing the Package](#installing-the-package)
- [Overview](#overview)
- [Launching the whole system](#launching-the-whole-system)
- [Launch arguments](#launch-arguments)
- [Launching a single node](#launching-a-single-node)
  - [resource_monitor_py/cpp](#resource_monitor_pycpp)
  - [resource_diagnostics_updater_py/cpp](#resource_diagnostics_updater_pycpp)
- [Configuration](#configuration)
  - [Telegraf config](#telegraf-config)
  - [Collectd config](#collectd-config)
  - [Diagnostics config](#diagnostics-config)
- [The documentation](#the-documentation)

## Installation

### Prerequisites

- ROS 2 Humble
- (OPTIONAL) lm-sensors, for temperature monitoring with telegraf. Collectd does not need it.

### Installing the Package

1. **Clone the repository** into your ROS 2 workspace:

   ```bash
   cd ~/ros2_ws/src
   git clone https://github.com/Bart-van-Ingen/resource_diagnostics_monitor.git
   ```

1. **Install dependencies**:

   ```bash
   cd ~/ros2_ws
   rosdep update
   rosdep install --from-paths src --ignore-src -r -y
   ```

1. **Build the package**:

   ```bash
   colcon build
   ```

1. **Source the workspace**:
   ```bash
   source install/setup.bash
   ```

## Overview

The architecture of these package is summarized in the following diagram and further explained in
the accompanying documentation
[architecture](https://bart-van-ingen.github.io/resource_diagnostics_monitor/architecture/) page.

<p align="center">
   <img src=".docs/images/architecture_diagram.drawio.svg" alt="Resource Monitor Diagram" />
</p>

## Launching the whole system

`resource_diagnostics_monitor_bringup` starts the resource monitor node, the diagnostics updater
node and a metric collector together. Pick the launch file for the implementation you want:

<details>
<summary><b>Python version</b></summary>

```bash
ros2 launch resource_diagnostics_monitor_bringup resource_diagnostics_monitor_py_launch.py monitor_type:=collectd
```

The `monitor_type` argument selects the metric collector: `telegraf` (default) or `collectd`.

This starts the `resource_monitor_py` node and the `resource_diagnostics_updater_py` node. Each
node runs in its own process.

</details>

<details>
<summary><b>C++ version</b></summary>

```bash
ros2 launch resource_diagnostics_monitor_bringup resource_diagnostics_monitor_cpp_launch.py monitor_type:=collectd
```

The `monitor_type` argument selects the metric collector: `telegraf` (default) or `collectd`.

This loads both C++ nodes as components into one `component_container` process, with
intra-process communication turned on. See
[Composable Nodes](https://bart-van-ingen.github.io/resource_diagnostics_monitor/learnings/composable_nodes/)
and
[Intra-Process Communication](https://bart-van-ingen.github.io/resource_diagnostics_monitor/learnings/intra_process_communication/).

</details>  

The metric collector is not started right away. The launch file waits until the node created its unix socket,
then starts the collector. Telegraf exits if it cannot connect to the socket.

## Launch arguments

All launch files share the same arguments. Defaults point at the files installed by
`resource_diagnostics_utils`, so no argument is needed for a default run.

| Argument               | Default                                                       | Available in                                    |
| ---------------------- | ------------------------------------------------------------- | ----------------------------------------------- |
| `log_level`            | `INFO`                                                        | all launch files                                |
| `config_file_path`     | `resource_diagnostics_utils/config/resource_diagnostics.yaml` | all launch files                                |
| `monitor_type`         | `telegraf`                                                    | all launch files that start a metric collector  |
| `telegraf_config_path` | `resource_diagnostics_utils/config/telegraf.conf`             | all launch files that start telegraf            |
| `collectd_config_path` | `resource_diagnostics_utils/config/collectd.conf`             | all launch files that start collectd            |
| `socket_path`          | `/tmp/metric_collector.sock`                                  | all launch files that start a metric collector  |

`socket_path` sets the `socket_path` node parameter and is used to wait for the socket before the
metric collector starts. It must match the `outputs.socket_writer` address in the telegraf config
and the `SocketPath` option in the collectd config.

Example with your own files and debug logging:

```bash
ros2 launch resource_diagnostics_monitor_bringup resource_diagnostics_monitor_cpp_launch.py \
    config_file_path:=/path/to/your/resource_diagnostics.yaml \
    telegraf_config_path:=/path/to/your/telegraf.conf \
    log_level:=DEBUG
```

Use `ros2 launch <package> <launch file> -s` to list the arguments of a launch file.

## Launching a single node

### resource_monitor_py/cpp

Receives the metrics of the metric collector over a unix socket and publishes the resources over
ROS 2 topics. Both launch files also start the metric collector. The `monitor_type` argument
selects it: `telegraf` (default) or `collectd`.

<details>
<summary><b>Python version</b></summary>

```bash
ros2 launch resource_monitor_py resource_monitor_launch.py
```

</details>

<details>
<summary><b>C++ version</b></summary>

```bash
ros2 launch resource_monitor_cpp resource_monitor_launch.py
```

</details>

### resource_diagnostics_updater_py/cpp

Subscribes to the resource topics and publishes diagnostics to `/diagnostics`. Both
implementations run a `resource_diagnostics_updater_node` and read the same `diagnosed_resources`
config format.

<details>
<summary><b>Python version</b></summary>

```bash
ros2 launch resource_diagnostics_updater_py resource_diagnostics_updater_launch.py
```

</details>

<details>
<summary><b>C++ version</b></summary>

The C++ package ships no launch file of its own. Run the node directly with a params file:

```bash
ros2 run resource_diagnostics_updater_cpp resource_diagnostics_updater_node \
    --ros-args --params-file /path/to/resource_diagnostics.yaml
```

To run it together with the C++ resource monitor, use
`resource_diagnostics_monitor_cpp_launch.py` from the bringup package.

</details>

## Configuration

All config files live in `resource_diagnostics_utils/config/` and are shared by the Python and the
C++ implementation. Colcon copies them into the install space, so edits to the source files only
take effect after a rebuild. Build with `colcon build --symlink-install` if you want to edit them
in place.

### Telegraf config

`resource_diagnostics_utils/config/telegraf.conf`:

- Collects metrics every 100 millisecond (configurable per input)
- Outputs data to unix socket `/tmp/metric_collector.sock`
- Includes processors for data cleanup and tagging
- Monitors CPU, memory, disk, sensors, and ROS processes

Pass `telegraf_config_path` to use a different file.

Look at the [influx plugins](https://docs.influxdata.com/telegraf/v1/plugins/) to find other
plugins that can monitor relevant resources for you.

### Collectd config

`resource_diagnostics_utils/config/collectd.conf`:

- Collects metrics every 0.2 seconds (`Interval`)
- Outputs data to unix socket `/tmp/metric_collector.sock` with the `collectd_socket_writer` plugin from
  this repository
- Monitors CPU, memory, disk, thermal zones, and ROS processes

Pass `collectd_config_path` to use a different file.

Look at the [collectd reference](https://bart-van-ingen.github.io/collectd_unofficial_reference/)
to find other plugins that can monitor relevant resources for you.

### Diagnostics config

`resource_diagnostics_utils/config/resource_diagnostics.yaml` specifies which resources to monitor
and their diagnostic thresholds. Pass `config_file_path` to use a different file.

The configuration file uses the following format:

```yaml
/resource_diagnostics_updater_node:
  ros__parameters:
    diagnosed_resources: |
      - topic: <topic name of resource to monitor>
        name: <name to show in diagnostics>
        field: <field to monitor>
        warning_threshold: <value for warning threshold>
        error_threshold: <value for error threshold>
```

The same file is given to both nodes in the bringup launch files. Each node picks up its own
section by node name.

## The documentation

The more detailed documentation is deployed using mkdocs. To run it on your local device, run the
following terminal command:

```bash
uv run --directory src --group docs mkdocs serve -a 127.0.0.1:8001
```
