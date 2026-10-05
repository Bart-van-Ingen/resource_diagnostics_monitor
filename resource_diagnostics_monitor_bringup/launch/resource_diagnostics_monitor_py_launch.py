from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import EqualsSubstitution, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

from resource_diagnostics_utils.launch_arguments import declare_config_file_path, declare_log_level
from resource_diagnostics_utils.monitor_launch_actions import collectd_actions, telegraf_actions


def generate_launch_description():
    resource_diagnostics_updater_py_launch_dir = PathJoinSubstitution(
        [FindPackageShare('resource_diagnostics_updater_py'), 'launch']
    )

    return LaunchDescription(
        [
            declare_log_level(),
            declare_config_file_path(),
            DeclareLaunchArgument(
                name='monitor_type',
                default_value='telegraf',
                choices=['telegraf', 'collectd'],
                description='the type of monitor to launch, options: telegraf, collectd',
            ),
            IncludeLaunchDescription(
                PathJoinSubstitution(
                    [
                        resource_diagnostics_updater_py_launch_dir,
                        'resource_diagnostics_updater_launch.py',
                    ]
                ),
                launch_arguments={
                    'config_file_path': LaunchConfiguration('config_file_path'),
                    'log_level': LaunchConfiguration('log_level'),
                }.items(),
            ),
            # started directly, because resource_monitor_launch.py always starts telegraf
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
                parameters=[LaunchConfiguration('config_file_path')],
            ),
            GroupAction(
                actions=telegraf_actions(),
                scoped=False,
                condition=IfCondition(
                    EqualsSubstitution(LaunchConfiguration('monitor_type'), 'telegraf')
                ),
            ),
            GroupAction(
                actions=collectd_actions(),
                scoped=False,
                condition=IfCondition(
                    EqualsSubstitution(LaunchConfiguration('monitor_type'), 'collectd')
                ),
            ),
        ]
    )
