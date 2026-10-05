# Composable Nodes

## What a composable node is

A composable node (a "component") is a node built as a shared library plugin instead of an
executable with its own `main()`. A container process loads one or more of these plugins at
runtime. This lets you decide at launch time whether nodes run as separate processes or share one
process [[1]](https://docs.ros.org/en/humble/Concepts/Intermediate/About-Composition.html).

In this repo, `resource_monitor_cpp` and `resource_diagnostics_updater_cpp` both build a
component. They can run:

- As separate processes, with `ros2 run`, exactly as before, or
- Together in one container process, via the composed launch file.

## Why use them

- **Faster communication.** Nodes in the same process can pass messages as pointers
  ([intra-process communication](intra_process_communication.md)). When publishing with
  `std::unique_ptr` this gives zero-copy transport: the subscriber receives the same message
  instance that was published, no serialization, no copy through DDS
  [[2]](https://docs.ros.org/en/humble/Tutorials/Demos/Intra-Process-Communication.html). Our two
  nodes form one pipeline (monitor publishes, updater subscribes), so this handoff can be nearly
  free.
- **Less overhead.** The ROS docs describe composition as "running multiple nodes in a single
  process with the lower overhead and optionally more efficient communication"
  [[1]](https://docs.ros.org/en/humble/Concepts/Intermediate/About-Composition.html). Every process
  carries its own DDS participant, threads, and memory, so one container with several components
  uses less RAM and CPU than the same nodes as separate processes.
- **The choice stays open.** This is the main point. The process layout is a deploy-time decision,
  not a coding decision
  [[1]](https://docs.ros.org/en/humble/Concepts/Intermediate/About-Composition.html). The decision
  moves out of the code and into the launch file. The same binary works both ways: run a node alone
  while debugging, compose everything in production.
- **Runtime flexibility.** Components can be loaded and unloaded into a running container with
  `ros2 component load` / `unload`, without restarting anything else
  [[3]](https://docs.ros.org/en/humble/Tutorials/Intermediate/Composition.html).

Trade-offs to keep in mind:

- One crashing component takes down the whole container, including the other nodes in it.
- Components share the container's executor. A component that blocks a callback for a long time can
  starve the others. (Our resource monitor node avoids this by doing its socket work in its own
  threads.)
- Logs from all components end up mixed in one process output.

## How our components are implemented and built

The component classes do **not** inherit from `rclcpp::Node`. Each one owns a plain node and hands
out its base interface. This works because `rclcpp_components` asks for only two things: a
constructor taking `rclcpp::NodeOptions`, and a `get_node_base_interface()` method. Inheriting from
`rclcpp::Node` is the common way to satisfy that, not the contract itself.

Each package builds three targets: the existing logic library with `-fPIC`, a shared library
holding the component source, and an executable that
`rclcpp_components_register_node(... EXECUTABLE ...)` generates.

## How to run

Separate processes, as before:

```bash
ros2 run resource_monitor_cpp resource_monitor_node
ros2 run resource_diagnostics_updater_cpp resource_diagnostics_updater_node
```

Both nodes in one process, plus telegraf:

```bash
ros2 launch resource_diagnostics_monitor_bringup resource_diagnostics_monitor_cpp_launch.py \
    config_file_path:=/path/to/resource_diagnostics.yaml
```

The config file is passed to both components. Each node picks up its own section by node name, same
as before.

Manual composition, without a launch file:

```bash
ros2 run rclcpp_components component_container
ros2 component load /ComponentManager resource_monitor_cpp ResourceMonitorNode
ros2 component load /ComponentManager resource_diagnostics_updater_cpp ResourceDiagnosticsUpdaterNode
```

`ros2 component types` lists the components a sourced workspace provides
[[3]](https://docs.ros.org/en/humble/Tutorials/Intermediate/Composition.html).

## Sources

1. [ROS 2 concept page: Composition](https://docs.ros.org/en/humble/Concepts/Intermediate/About-Composition.html)
2. [ROS 2 demo: Intra-process communication](https://docs.ros.org/en/humble/Tutorials/Demos/Intra-Process-Communication.html)
3. [ROS 2 tutorial: Composing multiple nodes in a single process](https://docs.ros.org/en/humble/Tutorials/Intermediate/Composition.html)
4. [ROS 2 how-to guide: Using ROS 2 launch to launch composable nodes](https://docs.ros.org/en/humble/How-To-Guides/Launching-composable-nodes.html)
