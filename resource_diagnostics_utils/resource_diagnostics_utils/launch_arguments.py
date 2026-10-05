from launch.actions import DeclareLaunchArgument

from resource_diagnostics_utils.default_paths import (
    DEFAULT_COLLECTD_CONFIG_PATH,
    DEFAULT_DIAGNOSTIC_CONFIG_PATH,
    DEFAULT_SOCKET_PATH,
    DEFAULT_TELEGRAF_CONFIG_PATH,
)


def declare_log_level():
    return DeclareLaunchArgument(
        name='log_level',
        default_value='INFO',
        description='log level of the nodes started by this launch file.',
    )


def declare_config_file_path():
    return DeclareLaunchArgument(
        name='config_file_path',
        default_value=DEFAULT_DIAGNOSTIC_CONFIG_PATH,
        description='Path to client specific yaml config file.',
    )


def declare_monitor_type():
    return DeclareLaunchArgument(
        name='monitor_type',
        default_value='telegraf',
        choices=['telegraf', 'collectd'],
        description='the type of monitor to launch, options: telegraf, collectd',
    )


def declare_telegraf_config_path():
    return DeclareLaunchArgument(
        name='telegraf_config_path',
        default_value=DEFAULT_TELEGRAF_CONFIG_PATH,
        description='Path to the telegraf config file telegraf is started with.',
    )


def declare_collectd_config_path():
    return DeclareLaunchArgument(
        name='collectd_config_path',
        default_value=DEFAULT_COLLECTD_CONFIG_PATH,
        description='Path to the collectd config file collectd is started with.',
    )


def declare_socket_path():
    return DeclareLaunchArgument(
        name='socket_path',
        default_value=DEFAULT_SOCKET_PATH,
        description=(
            'Path of the unix socket the node creates. It must '
            'match the outputs.socket_writer address in the telegraf config and the '
            'SocketPath option in the collectd config.'
        ),
    )
