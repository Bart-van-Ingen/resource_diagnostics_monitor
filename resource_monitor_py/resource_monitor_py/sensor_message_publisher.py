from rclpy._rclpy_pybind11 import RCLError  # ty: ignore[unresolved-import]
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time

from resource_monitor_interfaces.msg import Field, Resource

from resource_monitor_py.sensor_message import SensorMessage


class SensorMessagePublisher:
    def __init__(self, node: Node, message: SensorMessage) -> None:
        self.node = node
        self.logger = node.get_logger()

        sensor_type = message.name
        sensor_tags = message.tags

        # Convert tags dict to a pathed string
        tags_str = '/'.join(f'{value}' for value in sensor_tags.values()) if sensor_tags else ''

        topic_name = f'{sensor_type}/{tags_str}'

        # sanitize topic name to avoid issues with special characters
        topic_name = topic_name.replace(' ', '_').replace('-', '_')

        # remove trailing slashes
        topic_name = topic_name.rstrip('/')
        topic_name = topic_name.lower()

        self.logger.info(f'creating publisher for resource {topic_name}')

        self.publisher = node.create_publisher(
            msg_type=Resource,
            topic=topic_name,
            qos_profile=qos_profile_sensor_data,
        )

    def publish(self, message: SensorMessage) -> None:
        fields = []

        for field_name, field_value in message.fields.items():
            field_msg = Field()
            field_msg.name = field_name
            field_msg.value = float(field_value)
            fields.append(field_msg)

        resource_msg = Resource()
        resource_msg.header.stamp = Time(nanoseconds=message.timestamp).to_msg()
        resource_msg.fields = fields

        try:
            self.publisher.publish(resource_msg)
        except RCLError as e:
            if "publisher's context is invalid" in str(e):
                return
