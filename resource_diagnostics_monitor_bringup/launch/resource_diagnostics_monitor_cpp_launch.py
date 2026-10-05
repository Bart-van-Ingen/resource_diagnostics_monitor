from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

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
            ComposableNodeContainer(
                name='resource_monitor_container',
                namespace='',
                package='rclcpp_components',
                executable='component_container',
                output={'both': {'screen', 'log', 'own_log'}},
                emulate_tty=True,
                ros_arguments=[
                    '--log-level',
                    ['resource_monitor_node:=', LaunchConfiguration('log_level')],
                    '--log-level',
                    ['resource_diagnostics_updater_node:=', LaunchConfiguration('log_level')],
                ],
                composable_node_descriptions=[
                    ComposableNode(
                        package='resource_monitor_cpp',
                        plugin='ResourceMonitorNode',
                        name='resource_monitor_node',
                        parameters=[
                            LaunchConfiguration('config_file_path'),
                            {'socket_path': LaunchConfiguration('socket_path')},
                        ],
                        # both nodes need this, otherwise the messages go through DDS.
                        # see .docs/intra_process_communication.md
                        extra_arguments=[{'use_intra_process_comms': True}],
                    ),
                    ComposableNode(
                        package='resource_diagnostics_updater_cpp',
                        plugin='ResourceDiagnosticsUpdaterNode',
                        name='resource_diagnostics_updater_node',
                        parameters=[LaunchConfiguration('config_file_path')],
                        extra_arguments=[{'use_intra_process_comms': True}],
                    ),
                ],
            ),
            *monitor_type_actions(),
        ]
    )
