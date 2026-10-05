from pathlib import Path

import pytest

import rclpy
from rclpy.node import Node

from resource_monitor_py.sensor_message import SensorMessageBuffer
from resource_monitor_py.sensor_message_processor import SensorMessageProcessor
from resource_monitor_py.unix_socket_manager import UnixSocketManager


@pytest.fixture
def test_node():
    rclpy.init()
    test_node = Node('test_resource_monitor_node')

    yield test_node

    test_node.destroy_node()
    rclpy.shutdown()


# smoke test to make it initialize without error
def test_resource_monitor_node_initialization(test_node: Node, tmp_path: Path):
    logger = test_node.get_logger()

    sensor_message_buffer = SensorMessageBuffer(logger, max_buffer_size=100)

    # Initialize components
    unix_socket_manager = UnixSocketManager(
        logger, sensor_message_buffer, str(tmp_path / 'test.sock')
    )
    sensor_message_processor = SensorMessageProcessor(test_node, sensor_message_buffer)

    # Verify initialization worked
    assert sensor_message_processor.shutdown_event is not None
    assert unix_socket_manager.shutdown_event is not None
    assert sensor_message_processor.publisher_thread is not None
    assert unix_socket_manager.listener_thread is not None

    sensor_message_processor.shutdown()
    unix_socket_manager.shutdown()

    # Verify initialization worked
    assert not sensor_message_processor.publisher_thread.is_alive()
    assert not unix_socket_manager.listener_thread.is_alive()
