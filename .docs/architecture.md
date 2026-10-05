# Architecture

The repository contains these ROS 2 packages:

- `resource_monitor_py` and `resource_monitor_cpp`  
  Both Python and CPP implementation integrates a metric collector (Telegraf or collectd) with
  ROS 2 to monitor system resources and publish them as ROS messages. Their architecture is the same, but there are some differences in
  the details, which are called out below.
- `resource_diagnostics_updater_py` and `resource_diagnostics_updater_cpp`  
  Subscribes to resource topics and updates the ROS 2 diagnostics system with the latest metrics,
  based on target resources stipulated in a configuration file.
- `resource_monitor_interfaces`  
  Custom message definitions for resource monitoring.
- `resource_diagnostics_utils`  
  Holds what the other packages share: the config files and the launch helpers.
- `resource_diagnostics_monitor_bringup`  
  Launch files that start a monitor node, an updater node and a metric collector together.
- `telegraf_vendor`  
  Provides the Telegraf binary. See [vendor_packages](learnings/vendor_packages.md).
- `collectd_vendor`  
  Builds collectd from source and provides the collectd binary.
- `collectd_socket_writer`  
  A collectd write plugin that sends the metrics to the unix socket of the node.

The architecture between the packages is illustrated below:

<p align="center">
   <img src="../images/architecture_diagram.drawio.svg" alt="Resource Monitor Diagram" width="70%" />
</p>

### resource_monitor_py/cpp

This package interfaces with the metric collector over a unix socket and publishes the resources
over ROS2 topics. The node does not know which collector writes to the socket. Both collectors send
the same JSON format: one line per metric, with `name`, `timestamp`, `tags` and `fields`.

The package consists of:

- **Unix Socket Manager**: Receives JSON data from the metric collector via Unix socket
- **Sensor Message Processor**: Processes incoming sensor data and manages publishers
- **Sensor Message Publisher**: Publishes resource data as ROS 2 messages

#### Data Flow and Buffering

<p align="center">
   <img src="../images/data-flow.drawio.svg" alt="Resource Monitor Data Flow" />
</p>

The read thread splits the incoming byte stream into lines and puts them on a queue inside the
node. The processor thread takes them off the queue and publishes them, so the socket is drained
quickly no matter how slow publishing is.

The two implementations split the work slightly differently:

- **C++**: the read thread uses `getline` and pushes the raw string onto the queue. JSON parsing
  happens on the processor thread, in `SensorMessageBuffer::get_message`.
- **Python**: the read thread uses `recv` and splits on newlines itself. JSON parsing happens on
  that same read thread, in `SensorMessageBuffer.add_message`, so the queue holds parsed
  `SensorMessage` objects rather than strings.

Note that there are two buffers. The kernel already buffers the Unix socket and blocks Telegraf's
`write()` when full rather than dropping data. The queue absorbs bursts: Telegraf writes on its
`flush_interval`, not its `interval`, so an `interval` of `100ms` with a `flush_interval` of `1s`
would deliver a whole second of lines at once. Since `telegraf.conf` belongs to whoever installs
the package, the queue keeps the node tolerant of different setups. It does not help with sustained
overload, where the input rate exceeds what the node can publish.

The queues also behave differently under overload:

- **C++**: the queue is bounded by the `max_buffer_size` parameter (default 100). When it is full,
  the oldest message is dropped and a warning is logged.
- **Python**: the queue is unbounded, so it grows instead of dropping.

#### Topics Published

The package dynamically creates topics based on the metrics collected by the metric collector. This
is set by the collector config in `resource_diagnostics_utils/config/` (`telegraf.conf` or
`collectd.conf`).

**Examples** with the default `telegraf.conf` include:

- `/cpu/cpu0`
- `/cpu/cpu1`
- `/cpu/cpu2`
- `/cpu/cpu3`
- `/cpu/cpu_total`
- `/disk/root`
- `/mem`
- `/procstat/resource_monitor_node`
- `/sensors/acpitz_acpi_0/temp1`
- `/sensors/amdgpu_pci_0400/edge`
- `/sensors/amdgpu_pci_0400/slowppt`
- `/sensors/amdgpu_pci_0400/vddgfx`
- `/sensors/amdgpu_pci_0400/vddnb`
- `/sensors/bat1_acpi_0/in0`
- `/sensors/iwlwifi_1_virtual_0/temp1`
- `/sensors/k10temp_pci_00c3/tctl`
- `/sensors/nvme_pci_0100/composite`
- `/sensors/nvme_pci_0100/sensor_1`

Each topic publishes `Resource` messages from the
[resource_monitor_interfaces](#resource_monitor_interfaces) package.

**No topic configuration is needed on the node side**, since it will parse the available fields
from the messages it gets from the metric collector over the socket and use its names to generate
the topics accordingly. The nodes do declare a few ROS parameters:

| Parameter         | Default                      | Packages   | Description                                                                                                                                                             |
| ----------------- | ---------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `socket_path`     | `/tmp/metric_collector.sock` | py and cpp | Path of the Unix socket the node creates and the metric collector writes to. Must match `outputs.socket_writer` in `telegraf.conf` or `SocketPath` in `collectd.conf`. |
| `max_buffer_size` | `100`                        | cpp only   | Maximum number of queued lines before the oldest is dropped.                                                                                                            |

### resource_diagnostics_updater_py/cpp

Both the Python and C++ implementation share the same architecture. The package consists of:

- **Diagnostics Resource Updater**: Subscribes to specific resource topics and updates the ROS 2
  diagnostics system based on specified DiagnosedResource defined in the node configuration file,
  which is parsed at initialization.
- **Diagnostics Resource Updater Node**: Parses a configuration file to determine which resources
  to monitor and initializes the Diagnostics Resource Updaters accordingly.
- **Diagnostics Publisher**: Publishes aggregated diagnostics information to the `/diagnostics`
  topic at 1 Hz and is an interface to the diagnostics topic for the updaters. An updater that goes
  to warning or error level publishes straight away instead of waiting for the next timer tick.

Both implementations use the same `diagnosed_resources` config format. The C++ node also builds as
a composable node, so it can share one process with the C++ resource monitor (see
[Composable Nodes](learnings/composable_nodes.md)). The Python package ships a standalone launch
file; the C++ package ships none, because it is started from the composed bringup launch file.

### resource_monitor_interfaces

Defines custom ROS 2 message types for messages sent by the
[resource_monitor_py/cpp](#resource_monitor_pycpp) packages, including:

- `Field.msg`: Represents a single metric field with name and value
- `Resource.msg`: Represents a resource with a header and an array of `Field` messages

### collectd_socket_writer

A collectd write plugin, loaded with `LoadPlugin collectd_socket_writer` in `collectd.conf`. The
`SocketPath` option sets the socket it writes to.

collectd dispatches one measurement in several parts, one per type and type instance (for example
one per CPU state). The plugin collects the parts that have the same plugin and plugin instance, and
sends them as one JSON line when the next collection cycle starts. The field names contain the type
instance, the data source name and the type, so the values stay apart in one message.

If the plugin instance has fewer than 3 characters, the plugin name is added in front of it in the
`instance` tag (for example `cpu_0`). A short instance is likely a number, which cannot be used
directly in a topic name.

### Launch and config layout

`resource_diagnostics_utils` holds all config files and the launch helpers, so the Python and the
C++ side use one copy of each:

- `config/telegraf.conf`, `config/collectd.conf` and `config/resource_diagnostics.yaml`.
- `launch_arguments.py`, which declares the shared launch arguments: `log_level`,
  `config_file_path`, `monitor_type`, `telegraf_config_path`, `collectd_config_path` and
  `socket_path`.
- `monitor_launch_actions.py`, which starts the metric collector that `monitor_type` selects
  (`telegraf` or `collectd`). It waits for the node to create its unix socket, and only then starts
  the collector. Telegraf exits if it starts before the socket exists.
- `default_paths.py`, which resolves the config files, the default socket path and the Telegraf
  and collectd binaries in the install space.

`resource_diagnostics_monitor_bringup` builds on that with one launch file per implementation:

| Launch file                                  | What it starts                                                                                 |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `resource_diagnostics_monitor_py_launch.py`  | Starts the two Python nodes directly. One process per node.                                    |
| `resource_diagnostics_monitor_cpp_launch.py` | Loads both C++ components into one `component_container`, with intra-process communication on. |

Both also start the metric collector that `monitor_type` selects.
