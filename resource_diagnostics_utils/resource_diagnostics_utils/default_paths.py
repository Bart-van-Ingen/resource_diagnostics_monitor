from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackagePrefix, FindPackageShare


# sets the socket_path node parameter, must match outputs.socket_writer in the telegraf config
DEFAULT_SOCKET_PATH = '/tmp/metric_collector.sock'

# the single telegraf config for both implementations lives in this package
DEFAULT_TELEGRAF_CONFIG_PATH = PathJoinSubstitution(
    [FindPackageShare('resource_diagnostics_utils'), 'config', 'telegraf.conf']
)

DEFAULT_COLLECTD_CONFIG_PATH = PathJoinSubstitution(
    [FindPackageShare('resource_diagnostics_utils'), 'config', 'collectd.conf']
)

# the single diagnostics config for both implementations lives in this package
DEFAULT_DIAGNOSTIC_CONFIG_PATH = PathJoinSubstitution(
    [FindPackageShare('resource_diagnostics_utils'), 'config', 'resource_diagnostics.yaml']
)

# resolved directly instead of through PATH, so this also works without a sourced setup.bash
TELEGRAF_BIN = PathJoinSubstitution([FindPackagePrefix('telegraf_vendor'), 'bin', 'telegraf'])

COLLECTD_BIN = PathJoinSubstitution([FindPackagePrefix('collectd_vendor'), 'bin', 'collectd'])
