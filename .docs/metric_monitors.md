# Metric Monitors

This package supports two metric collectors: Telegraf and collectd. Each has advantages and
disadvantages, so the user can select the one that fits the robot. Select it with the
`monitor_type` launch argument (`telegraf` or `collectd`).

## Comparison

### Telegraf

Advantages:

- **Better documentation.** The
  [Telegraf plugin documentation](https://docs.influxdata.com/telegraf/v1/plugins/) is better than
  the official collectd documentation.
- **Connects to other metric systems.** Telegraf has more than 300 plugins. Its output plugins can
  send the same metrics to other exporters and backends, for example over OTLP to an
  [OpenTelemetry collector](https://opentelemetry.io/docs/collector/distributions/).
- **Active development.** Telegraf releases often. The latest release is v1.40.1 (2026-09-21).
- **No compile step.** `telegraf_vendor` downloads a prebuilt binary, or uses a `telegraf` that is
  already installed.
- **Filters before it sends.** Options such as `fieldinclude` drop fields before they reach the
  socket, so the node gets less data.
- **Per CPU and total at the same time.** collectd can only report one of the two.

Disadvantages:

- **Large binary.** The full Telegraf 1.35.3 binary is about 290 MB, because it contains all
  plugins. See [Reduce the Telegraf binary size](#reduce-the-telegraf-binary-size).
- **Written in Go.** Go is not one of the main ROS 2 languages (C++ and Python). To change or
  extend Telegraf itself, you must know Go.
- **More resources.** A test with the same configs for both collectors measured these values:

  | Collector | CPU [% of one core] | RAM (RSS) [MiB] |
  | --------- | ------------------- | --------------- |
  | collectd  | 2.67                | 4.3             |
  | telegraf  | 10.76               | 149.0           |

  For the same work, Telegraf used about 4 times more CPU and about 35 times more RAM.
- **External program for sensors.** The `sensors` input runs the `sensors` program, so it needs
  lm-sensors installed.

#### Reduce the Telegraf binary size

Telegraf has a custom builder tool. It reads your config file and builds a binary that contains
only the plugins in that config. In the example of InfluxData, the binary went from 207.9 MB to
17.6 MB. See [How to reduce Telegraf binary size](https://www.influxdata.com/blog/how-reduce-telegraf-binary-size/).

This repository does not do this for you. The result depends on the config of each user, so it is
out of scope. Build the binary yourself and install it as `telegraf` on the `PATH` before you build
the workspace. `telegraf_vendor` then uses it instead of downloading the full binary.

### collectd

Advantages:

- **Small.** The collectd daemon is about 0.6 MB. All plugins that this package builds are 4.8 MB
  together.
- **Fewer resources.** See the table above.
- **Written in C.** This is close to C++, one of the main ROS 2 languages. The
  `collectd_socket_writer` plugin of this repository is a C++ collectd plugin.

Disadvantages:

- **Less active development.** The last release is 5.12.0 (2020-09-03). The repository still gets
  commits, but there has been no new release since then.
- **Lacking documentation.** The official documentation is lacking. Use the
  [collectd unofficial reference](https://bart-van-ingen.github.io/collectd_unofficial_reference/)
  instead.
- **Built from source.** `collectd_vendor` downloads the source and compiles it, so the first
  workspace build takes longer.
- **Own write plugin necessary.** This repository maintains `collectd_socket_writer` to send the
  metrics to the node. Telegraf only needs its `outputs.socket_writer` plugin.
- **GPL-2.0 plugins.** Some plugins, for example `cpu`, `df`, `disk`, `memory`, `processes` and
  `thermal`, are GPL-2.0. Telegraf is MIT.

## collectd: which plugins are built

`collectd_vendor` builds every collectd plugin that needs no external library on Linux. The user
can then enable a plugin in the config file without a rebuild. The configure default (all plugins
on) is not used, because it silently drops each plugin whose library is missing. The plugin set
would then depend on which `-dev` packages are on the build machine.

The list was found like this:

1. In `configure.ac`, take each `AC_PLUGIN` whose condition is a fixed `yes`, a Linux-only check,
   or a kernel or libc header check. Skip each plugin that depends on a `with_lib*` variable.
2. Run `configure --disable-all-plugins` with an `--enable-X` for each plugin in the list, then run
   `make`. Both must pass.
3. Run `ldd` on each built plugin to check for extra libraries.

Three plugins use an optional library when it is present, and build without it when it is not:
`disk` (libudev), `network` (libgcrypt) and `processes` (libmnl).

### Plugin table

This table shows all 175 plugins of collectd 5.12.0:

- **Built**: `collectd_vendor` builds the plugin. You can load it without a rebuild.
- **Loaded**: the default `collectd.conf` loads the plugin, so it is active.
- **Needs**: what the plugin needs to build. For a plugin that is not built, this is the reason.

`collectd_socket_writer` is not in the table. It comes from this repository, not from collectd. The
default `collectd.conf` also loads it.

??? info "Plugin table (click to open)"

    | Plugin                | Description                                                                | Built | Loaded | Needs                                             |
    | --------------------- | -------------------------------------------------------------------------- | ----- | ------ | ------------------------------------------------- |
    | `aggregation`         | Aggregation plugin                                                         | yes   | no     |                                                   |
    | `amqp`                | AMQP output plugin                                                         | no    | no     | librabbitmq                                       |
    | `amqp1`               | AMQP 1.0 output plugin                                                     | no    | no     | libqpid_proton                                    |
    | `apache`              | Apache httpd statistics                                                    | no    | no     | libcurl                                           |
    | `apcups`              | Statistics of UPSes by APC                                                 | yes   | no     |                                                   |
    | `apple_sensors`       | Apple hardware sensors                                                     | no    | no     | libiokit (macOS only)                             |
    | `aquaero`             | Aquaero hardware sensors                                                   | no    | no     | libaquaero5                                       |
    | `ascent`              | AscentEmu player statistics                                                | no    | no     | libcurl, libxml2                                  |
    | `barometer`           | Barometer sensor on I2C                                                    | no    | no     | libi2c                                            |
    | `battery`             | Battery statistics                                                         | yes   | no     |                                                   |
    | `bind`                | ISC Bind nameserver statistics                                             | no    | no     | libcurl, libxml2                                  |
    | `buddyinfo`           | buddyinfo statistics                                                       | yes   | no     |                                                   |
    | `capabilities`        | Platform static capabilities                                               | no    | no     | libmicrohttpd, libjansson                         |
    | `ceph`                | Ceph daemon statistics                                                     | no    | no     | libyajl                                           |
    | `cgroups`             | CGroups CPU usage accounting                                               | yes   | no     |                                                   |
    | `chrony`              | Chrony statistics                                                          | yes   | no     |                                                   |
    | `check_uptime`        | Notify about uptime reset                                                  | yes   | no     |                                                   |
    | `connectivity`        | Network interface up/down events                                           | no    | no     | libyajl 2, libmnl                                 |
    | `conntrack`           | nf_conntrack statistics                                                    | yes   | no     |                                                   |
    | `contextswitch`       | context switch statistics                                                  | yes   | no     |                                                   |
    | `cpu`                 | CPU usage statistics                                                       | yes   | yes    |                                                   |
    | `cpufreq`             | CPU frequency statistics                                                   | yes   | no     |                                                   |
    | `cpusleep`            | CPU sleep statistics                                                       | yes   | no     |                                                   |
    | `csv`                 | CSV output plugin                                                          | yes   | no     |                                                   |
    | `curl`                | CURL generic web statistics                                                | no    | no     | libcurl                                           |
    | `curl_json`           | CouchDB statistics                                                         | no    | no     | libcurl, libyajl                                  |
    | `curl_xml`            | CURL generic xml statistics                                                | no    | no     | libcurl, libxml2                                  |
    | `dbi`                 | General database statistics                                                | no    | no     | libdbi                                            |
    | `dcpmm`               | Intel(R) Optane(TM) DC Persistent Memory performance and health statistics | no    | no     | libpmwapi                                         |
    | `df`                  | Filesystem usage statistics                                                | yes   | yes    |                                                   |
    | `disk`                | Disk usage statistics                                                      | yes   | yes    | libudev (optional)                                |
    | `dns`                 | DNS traffic analysis                                                       | no    | no     | libpcap                                           |
    | `dpdkevents`          | Events from DPDK                                                           | no    | no     | libdpdk 16.07 or newer                            |
    | `dpdkstat`            | Stats from DPDK                                                            | no    | no     | libdpdk                                           |
    | `dpdk_telemetry`      | Metrics from DPDK Telemetry                                                | no    | no     | libjansson                                        |
    | `drbd`                | DRBD statistics                                                            | yes   | no     |                                                   |
    | `email`               | EMail statistics                                                           | yes   | no     |                                                   |
    | `entropy`             | Entropy statistics                                                         | yes   | no     |                                                   |
    | `ethstat`             | Stats from NIC driver                                                      | yes   | no     |                                                   |
    | `exec`                | Execution of external programs                                             | yes   | no     |                                                   |
    | `fhcount`             | File handles statistics                                                    | yes   | no     |                                                   |
    | `filecount`           | Count files in directories                                                 | yes   | no     |                                                   |
    | `fscache`             | fscache statistics                                                         | yes   | no     |                                                   |
    | `gmond`               | Ganglia plugin                                                             | no    | no     | libganglia                                        |
    | `gps`                 | GPS plugin                                                                 | no    | no     | libgps                                            |
    | `gpu_nvidia`          | NVIDIA GPU plugin                                                          | no    | no     | CUDA                                              |
    | `grpc`                | gRPC plugin                                                                | no    | no     | libgrpc++, libprotobuf, protoc 3, grpc_cpp_plugin |
    | `hddtemp`             | Query hddtempd                                                             | yes   | no     |                                                   |
    | `hugepages`           | Hugepages statistics                                                       | yes   | no     |                                                   |
    | `infiniband`          | Infiniband statistics                                                      | yes   | no     |                                                   |
    | `intel_pmu`           | Intel performance monitor plugin                                           | no    | no     | libjevents                                        |
    | `intel_rdt`           | Intel RDT monitor plugin                                                   | no    | no     | libpqos                                           |
    | `interface`           | Interface traffic statistics                                               | yes   | no     |                                                   |
    | `ipc`                 | IPC statistics                                                             | yes   | no     |                                                   |
    | `ipmi`                | IPMI sensor statistics                                                     | no    | no     | libOpenIPMIpthread                                |
    | `iptables`            | IPTables rule counters                                                     | no    | no     | libiptc                                           |
    | `ipstats`             | IP packet statistics                                                       | no    | no     | FreeBSD only                                      |
    | `ipvs`                | IPVS connection statistics                                                 | yes   | no     |                                                   |
    | `irq`                 | IRQ statistics                                                             | yes   | no     |                                                   |
    | `java`                | Embed the Java Virtual Machine                                             | no    | no     | Java JDK                                          |
    | `load`                | System load                                                                | yes   | no     |                                                   |
    | `log_logstash`        | Logstash json_event compatible logging                                     | no    | no     | libyajl                                           |
    | `logfile`             | File logging plugin                                                        | yes   | yes    |                                                   |
    | `logparser`           | Log parsing plugin                                                         | yes   | no     |                                                   |
    | `lpar`                | AIX logical partitions statistics                                          | no    | no     | libperfstat (AIX only)                            |
    | `lua`                 | Lua plugin                                                                 | no    | no     | liblua                                            |
    | `madwifi`             | Madwifi wireless statistics                                                | yes   | no     |                                                   |
    | `match_empty_counter` | The empty counter match                                                    | yes   | no     |                                                   |
    | `match_hashed`        | The hashed match                                                           | yes   | no     |                                                   |
    | `match_regex`         | The regex match                                                            | yes   | no     |                                                   |
    | `match_timediff`      | The timediff match                                                         | yes   | no     |                                                   |
    | `match_value`         | The value match                                                            | yes   | no     |                                                   |
    | `mbmon`               | Query mbmond                                                               | yes   | no     |                                                   |
    | `mcelog`              | Machine Check Exceptions notifications                                     | yes   | no     |                                                   |
    | `md`                  | md (Linux software RAID) devices                                           | yes   | no     |                                                   |
    | `mdevents`            | Events from md (Linux Software RAID) devices                               | yes   | no     |                                                   |
    | `memcachec`           | memcachec statistics                                                       | no    | no     | libmemcached                                      |
    | `memcached`           | memcached statistics                                                       | yes   | no     |                                                   |
    | `memory`              | Memory usage                                                               | yes   | yes    |                                                   |
    | `mic`                 | Intel Many Integrated Core stats                                           | no    | no     | Intel MIC SDK                                     |
    | `modbus`              | Modbus plugin                                                              | no    | no     | libmodbus                                         |
    | `mqtt`                | MQTT output plugin                                                         | no    | no     | libmosquitto                                      |
    | `multimeter`          | Read multimeter values                                                     | yes   | no     |                                                   |
    | `mysql`               | MySQL statistics                                                           | no    | no     | libmysql                                          |
    | `netapp`              | NetApp plugin                                                              | no    | no     | libnetapp                                         |
    | `netlink`             | Enhanced Linux network statistics                                          | no    | no     | libmnl                                            |
    | `netstat_udp`         | UDP network statistics                                                     | no    | no     | NetBSD only                                       |
    | `network`             | Network communication plugin                                               | yes   | no     | libgcrypt (optional)                              |
    | `nfs`                 | NFS statistics                                                             | yes   | no     |                                                   |
    | `nginx`               | nginx statistics                                                           | no    | no     | libcurl                                           |
    | `notify_desktop`      | Desktop notifications                                                      | no    | no     | libnotify                                         |
    | `notify_email`        | Email notifier                                                             | no    | no     | libesmtp                                          |
    | `notify_nagios`       | Nagios notification plugin                                                 | yes   | no     |                                                   |
    | `ntpd`                | NTPd statistics                                                            | yes   | no     |                                                   |
    | `numa`                | NUMA virtual memory statistics                                             | yes   | no     |                                                   |
    | `nut`                 | Network UPS tools statistics                                               | no    | no     | libupsclient                                      |
    | `olsrd`               | olsrd statistics                                                           | yes   | no     |                                                   |
    | `onewire`             | OneWire sensor statistics                                                  | no    | no     | libowcapi                                         |
    | `openldap`            | OpenLDAP statistics                                                        | no    | no     | libldap                                           |
    | `openvpn`             | OpenVPN client statistics                                                  | yes   | no     |                                                   |
    | `oracle`              | Oracle plugin                                                              | no    | no     | Oracle client                                     |
    | `ovs_events`          | OVS events plugin                                                          | no    | no     | libyajl 2                                         |
    | `ovs_stats`           | OVS statistics plugin                                                      | no    | no     | libyajl 2                                         |
    | `pcie_errors`         | PCIe errors plugin                                                         | yes   | no     |                                                   |
    | `perl`                | Embed a Perl interpreter                                                   | no    | no     | libperl with ithreads                             |
    | `pf`                  | BSD packet filter (PF) statistics                                          | no    | no     | BSD only (net/pfvar.h)                            |
    | `pinba`               | Pinba statistics                                                           | no    | no     | libprotobuf-c, protoc-c                           |
    | `ping`                | Network latency statistics                                                 | no    | no     | liboping                                          |
    | `postgresql`          | PostgreSQL database statistics                                             | no    | no     | libpq                                             |
    | `powerdns`            | PowerDNS statistics                                                        | yes   | no     |                                                   |
    | `processes`           | Process statistics                                                         | yes   | yes    | libmnl (optional)                                 |
    | `procevent`           | Process event (start, stop) statistics                                     | no    | no     | libyajl 2                                         |
    | `protocols`           | Protocol (IP, TCP, ...) statistics                                         | yes   | no     |                                                   |
    | `python`              | Embed a Python interpreter                                                 | no    | no     | libpython                                         |
    | `redfish`             | Redfish plugin                                                             | no    | no     | libredfish                                        |
    | `redis`               | Redis plugin                                                               | no    | no     | libhiredis                                        |
    | `routeros`            | RouterOS plugin                                                            | no    | no     | librouteros                                       |
    | `rrdcached`           | RRDTool output plugin                                                      | no    | no     | librrd                                            |
    | `rrdtool`             | RRDTool output plugin                                                      | no    | no     | librrd                                            |
    | `sensors`             | lm_sensors statistics                                                      | no    | no     | libsensors                                        |
    | `serial`              | serial port traffic                                                        | yes   | no     |                                                   |
    | `sigrok`              | sigrok acquisition sources                                                 | no    | no     | libsigrok                                         |
    | `slurm`               | SLURM jobs and nodes status                                                | no    | no     | libslurm                                          |
    | `smart`               | SMART statistics                                                           | no    | no     | libatasmart, libudev                              |
    | `snmp`                | SNMP querying plugin                                                       | no    | no     | libnetsnmp                                        |
    | `snmp_agent`          | SNMP agent plugin                                                          | no    | no     | libnetsnmpagent                                   |
    | `statsd`              | StatsD plugin                                                              | yes   | no     |                                                   |
    | `swap`                | Swap usage statistics                                                      | yes   | no     |                                                   |
    | `synproxy`            | Synproxy stats plugin                                                      | yes   | no     |                                                   |
    | `sysevent`            | rsyslog events                                                             | no    | no     | libyajl                                           |
    | `syslog`              | Syslog logging plugin                                                      | yes   | no     |                                                   |
    | `table`               | Parsing of tabular data                                                    | yes   | no     |                                                   |
    | `tail`                | Parsing of logfiles                                                        | yes   | no     |                                                   |
    | `tail_csv`            | Parsing of CSV files                                                       | yes   | no     |                                                   |
    | `tape`                | Tape drive statistics                                                      | no    | no     | Solaris only                                      |
    | `target_notification` | The notification target                                                    | yes   | no     |                                                   |
    | `target_replace`      | The replace target                                                         | yes   | no     |                                                   |
    | `target_scale`        | The scale target                                                           | yes   | no     |                                                   |
    | `target_set`          | The set target                                                             | yes   | no     |                                                   |
    | `target_v5upgrade`    | The v5upgrade target                                                       | yes   | no     |                                                   |
    | `tcpconns`            | TCP connection statistics                                                  | yes   | no     |                                                   |
    | `teamspeak2`          | TeamSpeak2 server statistics                                               | yes   | no     |                                                   |
    | `ted`                 | Read The Energy Detective values                                           | yes   | no     |                                                   |
    | `thermal`             | Linux ACPI thermal zone statistics                                         | yes   | yes    |                                                   |
    | `threshold`           | Threshold checking plugin                                                  | yes   | no     |                                                   |
    | `tokyotyrant`         | TokyoTyrant database statistics                                            | no    | no     | libtokyotyrant                                    |
    | `turbostat`           | Advanced statistic on Intel cpu states                                     | yes   | no     |                                                   |
    | `ubi`                 | UBIFS statistics                                                           | yes   | no     |                                                   |
    | `unixsock`            | Unixsock communication plugin                                              | yes   | no     |                                                   |
    | `uptime`              | Uptime statistics                                                          | yes   | no     |                                                   |
    | `users`               | User statistics                                                            | yes   | no     |                                                   |
    | `uuid`                | UUID as hostname plugin                                                    | yes   | no     |                                                   |
    | `varnish`             | Varnish cache statistics                                                   | no    | no     | libvarnish                                        |
    | `virt`                | Virtual machine statistics                                                 | no    | no     | libvirt, libxml2                                  |
    | `vmem`                | Virtual memory statistics                                                  | yes   | no     |                                                   |
    | `vserver`             | Linux VServer statistics                                                   | yes   | no     |                                                   |
    | `wireless`            | Wireless statistics                                                        | yes   | no     |                                                   |
    | `write_graphite`      | Graphite / Carbon output plugin                                            | yes   | no     |                                                   |
    | `write_http`          | HTTP output plugin                                                         | no    | no     | libcurl                                           |
    | `write_influxdb_udp`  | Influxdb udp output plugin                                                 | yes   | no     |                                                   |
    | `write_kafka`         | Kafka output plugin                                                        | no    | no     | librdkafka                                        |
    | `write_log`           | Log output plugin                                                          | yes   | no     |                                                   |
    | `write_mongodb`       | MongoDB output plugin                                                      | no    | no     | libmongoc                                         |
    | `write_prometheus`    | Prometheus write plugin                                                    | no    | no     | libprotobuf-c, protoc-c, libmicrohttpd            |
    | `write_redis`         | Redis output plugin                                                        | no    | no     | libhiredis                                        |
    | `write_riemann`       | Riemann output plugin                                                      | no    | no     | libriemann_client                                 |
    | `write_sensu`         | Sensu output plugin                                                        | yes   | no     |                                                   |
    | `write_stackdriver`   | Google Stackdriver Monitoring output plugin                                | no    | no     | libcurl, libssl, libyajl 2                        |
    | `write_syslog`        | Syslog output plugin                                                       | yes   | no     |                                                   |
    | `write_tsdb`          | TSDB output plugin                                                         | yes   | no     |                                                   |
    | `xencpu`              | Xen Host CPU usage                                                         | no    | no     | libxenctrl                                        |
    | `xmms`                | XMMS statistics                                                            | no    | no     | libxmms                                           |
    | `zfs_arc`             | ZFS ARC statistics                                                         | yes   | no     |                                                   |
    | `zone`                | Solaris container statistics                                               | no    | no     | Solaris only                                      |
    | `zookeeper`           | Zookeeper statistics                                                       | yes   | no     |                                                   |

Refer to the [collectd unofficial reference](https://bart-van-ingen.github.io/collectd_unofficial_reference/)
for what each plugin does and how to configure it.

### Use a plugin that is already built

Add a `LoadPlugin` line and, if necessary, a `<Plugin>` block to `collectd.conf`. No rebuild is
necessary:

```
LoadPlugin load
```

### Add a plugin that needs an external library

1. Install the `-dev` package of the library. Also add it as a `<build_depend>` in
   `collectd_vendor/package.xml`, so that `rosdep` installs it on other machines.
2. Add `--enable-<plugin>` to the `configure` options in `collectd_vendor/CMakeLists.txt`.
3. Rebuild `collectd_vendor`. If the library is missing, `configure` stops with
   `Some plugins are missing dependencies`.
4. Load the plugin in `collectd.conf`.
