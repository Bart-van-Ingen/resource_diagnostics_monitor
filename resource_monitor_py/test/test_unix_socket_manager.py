import socket
from dataclasses import dataclass
from pathlib import Path

import pytest

import rclpy
from rclpy.node import Node

from resource_monitor_py.unix_socket_manager import (
    SensorMessageBuffer,
    UnixSocketManager,
)


@pytest.fixture
def test_unix_socket_manager(tmp_path: Path):
    rclpy.init()
    test_node = Node('test_sensor_message_node')
    logger = test_node.get_logger()
    sensor_message_buffer = SensorMessageBuffer(logger, max_buffer_size=100)
    unix_socket_manager = UnixSocketManager(
        logger, sensor_message_buffer, str(tmp_path / 'test.sock')
    )

    yield unix_socket_manager

    unix_socket_manager.shutdown()
    rclpy.shutdown()


@dataclass
class UnixSocketManagerTestParams:
    sent_chunks: list[str]
    expected_messages: list[str]


@pytest.mark.parametrize(
    'test_parameters',
    [
        pytest.param(
            UnixSocketManagerTestParams(
                sent_chunks=[
                    '{"fields":{"free":117752885248,"total":403028406272,'
                    '"used_percent":69.21337618804728},"name":"disk","tags":'
                    '{"path":"root"},"timestamp":1756879911}\n{"fields"'
                    ':{"memory_usage":0.2598787248134613},"name":"procstat","tags":'
                    '{"node_name":"resource_diagnostics_monitor"},"timestamp":1756879911}\n'
                ],
                expected_messages=[
                    '{"fields":{"free":117752885248,"total":403028406272,'
                    '"used_percent":69.21337618804728},"name":"disk","tags":'
                    '{"path":"root"},"timestamp":1756879911}',
                    '{"fields":{"memory_usage":0.2598787248134613},"name":"procstat","tags":'
                    '{"node_name":"resource_diagnostics_monitor"},"timestamp":1756879911}',
                ],
            ),
            id='2_complete_messages',
        ),
        pytest.param(
            UnixSocketManagerTestParams(
                sent_chunks=[
                    '{"fields":{"in_input":',
                    '1.206},"name":"sensors","tags":{"chip":"amdgpu-pci-0400",'
                    '"feature":"vddgfx"},"timestamp":1756879912}\n'
                    '{"fields":{"in_input":0.762},"name":"sensors",',
                    '"tags":{"chip":"amdgpu-pci-0400","feature":"vddnb"},'
                    '"timestamp":1756879912}\n',
                ],
                expected_messages=[
                    '{"fields":{"in_input":1.206},"name":"sensors","tags":'
                    '{"chip":"amdgpu-pci-0400","feature":"vddgfx"},"timestamp":1756879912}',
                    '{"fields":{"in_input":0.762},"name":"sensors","tags":'
                    '{"chip":"amdgpu-pci-0400","feature":"vddnb"},"timestamp":1756879912}',
                ],
            ),
            id='messages_split_over_chunks',
        ),
    ],
)
def test_handle_connection(
    test_unix_socket_manager: UnixSocketManager,
    test_parameters: UnixSocketManagerTestParams,
):
    server_conn, client_conn = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    with client_conn:
        for chunk in test_parameters.sent_chunks:
            client_conn.sendall(chunk.encode('utf-8'))

    # the client is closed, so handle_connection returns at end of stream
    test_unix_socket_manager.handle_connection(server_conn)

    sensor_message_buffer = test_unix_socket_manager.sensor_message_buffer
    assert list(sensor_message_buffer.buffer) == test_parameters.expected_messages
