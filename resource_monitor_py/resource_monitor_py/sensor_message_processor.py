import threading
from collections import defaultdict
from threading import Thread

from rclpy.node import Node

from resource_monitor_py.sensor_message import SensorMessage, SensorMessageBuffer
from resource_monitor_py.sensor_message_publisher import SensorMessagePublisher


class SensorMessageProcessor:
    def __init__(self, node: Node, sensor_message_buffer: SensorMessageBuffer) -> None:
        self.node = node
        self.sensor_message_buffer = sensor_message_buffer
        self.logger = node.get_logger()
        self.sensor_publishers = defaultdict(dict)

        # Add shutdown flag so that we can shutdown in unit testing
        self.shutdown_event = threading.Event()

        self.publisher_thread = Thread(target=self.process_buffered_messages)
        self.logger.debug('starting sensor publisher thread')
        self.publisher_thread.start()

    def shutdown(self):
        self.shutdown_event.set()

        # Only join if we're not calling from the same thread
        current_thread = threading.current_thread()
        if self.publisher_thread.is_alive() and self.publisher_thread != current_thread:
            self.publisher_thread.join(timeout=1.0)  # Wait max 1 second

    def process_buffered_messages(self) -> None:
        while not self.shutdown_event.is_set():
            message = self.sensor_message_buffer.get_message(timeout=0.1)
            if message is not None:
                self.publish_sensor_message(message)

    def publish_sensor_message(self, message: SensorMessage) -> None:

        self.logger.debug(f'publishing sensor message: {message.name} with tags: {message.tags}')
        sensor_message_publisher = self.get_publisher(message)
        sensor_message_publisher.publish(message)

    def get_publisher(self, message: SensorMessage) -> SensorMessagePublisher:

        sensor_type = message.name
        sensor_tags = message.tags

        # Convert tags dict to a hashable key
        tags_key = tuple(sorted(sensor_tags.items())) if sensor_tags else None

        # defaultdict automatically creates the inner dict if it doesn't exist
        if tags_key not in self.sensor_publishers[sensor_type]:
            self.sensor_publishers[sensor_type][tags_key] = SensorMessagePublisher(
                self.node, message
            )

        return self.sensor_publishers[sensor_type][tags_key]
