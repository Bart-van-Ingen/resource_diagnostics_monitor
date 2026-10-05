from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from resource_diagnostics_utils.launch_arguments import (
    declare_config_file_path,
    declare_log_level,
    declare_socket_path,
)
from resource_diagnostics_utils.monitor_launch_actions import monitor_type_actions


def generate_launch_description():
    return LaunchDescription(
        [
            declare_log_level(),
            declare_config_file_path(),
            declare_socket_path(),
            Node(
                package='resource_monitor_py',
                executable='resource_monitor_node',
                name='resource_monitor_node',
                output={'both': {'screen', 'log', 'own_log'}},
                emulate_tty=True,
                ros_arguments=[
                    '--log-level',
                    ['resource_monitor_node:=', LaunchConfiguration('log_level')],
                ],
                parameters=[
                    LaunchConfiguration('config_file_path'),
                    {'socket_path': LaunchConfiguration('socket_path')},
                ],
            ),
            *monitor_type_actions(),
        ]
    )
