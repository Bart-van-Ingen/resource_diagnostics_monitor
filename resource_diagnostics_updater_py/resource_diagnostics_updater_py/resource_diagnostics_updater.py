from diagnostic_msgs.msg import DiagnosticStatus, KeyValue
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.qos import qos_profile_sensor_data

from resource_monitor_interfaces.msg import Field, Resource

from resource_diagnostics_updater_py.diagnosed_resource import DiagnosedResource
from resource_diagnostics_updater_py.diagnostics_publisher import DiagnosticsPublisher


class ResourceDiagnosticsUpdater:
    def __init__(
        self,
        diagnostics_publisher: DiagnosticsPublisher,
        diagnosed_resource: DiagnosedResource,
        reentrant_callback_group: ReentrantCallbackGroup,
    ) -> None:

        self.diagnostics_publisher = diagnostics_publisher
        self.diagnosed_resource = diagnosed_resource

        # Create diagnostic status for this resource whose values will be updated in the callback
        self.diagnostic_status = DiagnosticStatus()
        self.diagnostic_status.level = DiagnosticStatus.STALE
        self.diagnostic_status.name = diagnosed_resource.name
        self.diagnostic_status.message = 'unknown'
        self.diagnostic_status.hardware_id = 'resource_diagnostics_monitor'

        # Register this diagnostic status with the diagnostics publisher so that it gets published
        #  at the publishers timer rate
        self.diagnostics_publisher.add_diagnostic_status(self.diagnostic_status)

        self.diagnostics_publisher.node.create_subscription(
            Resource,
            diagnosed_resource.topic,
            self.resource_callback,
            qos_profile_sensor_data,
            callback_group=reentrant_callback_group,
        )

        self.diagnostics_publisher.node.get_logger().info(
            f"subscribed to resource topic '{diagnosed_resource.topic}' for diagnostics."
        )

    def resource_callback(self, resource_message: Resource) -> None:

        diagnosed_resource_field: Field = next(
            field
            for field in resource_message.fields
            if field.name == self.diagnosed_resource.field
        )

        self.diagnostic_status.values = [
            KeyValue(
                key=diagnosed_resource_field.name,
                value=str(diagnosed_resource_field.value),
            )
        ]

        if diagnosed_resource_field.value >= self.diagnosed_resource.error_threshold:
            self.diagnostic_status.level = DiagnosticStatus.ERROR
            self.diagnostic_status.message = (
                f'error for {self.diagnosed_resource.name} ({self.diagnosed_resource.field}):'
                f' {diagnosed_resource_field.value} over error threshold'
                f' {self.diagnosed_resource.error_threshold}'
            )

        elif diagnosed_resource_field.value >= self.diagnosed_resource.warning_threshold:
            self.diagnostic_status.level = DiagnosticStatus.WARN
            self.diagnostic_status.message = (
                f'warning for {self.diagnosed_resource.name} ({self.diagnosed_resource.field}):'
                f' {diagnosed_resource_field.value} over warning threshold'
                f' {self.diagnosed_resource.warning_threshold}'
            )

        else:
            self.diagnostic_status.level = DiagnosticStatus.OK
            self.diagnostic_status.message = f'{self.diagnosed_resource.name} ok'
            return

        # only immediately publish if status is warning or error, otherwise it will be published at
        # the next timer event of the diagnostics publisher
        self.publish()

    def publish(self) -> None:
        self.diagnostics_publisher.publish_diagnostics(self.diagnostic_status)
