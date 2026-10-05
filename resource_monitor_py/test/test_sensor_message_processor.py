import json
from dataclasses import asdict, dataclass

import pytest

import rclpy
from rclpy.node import Node

from resource_monitor_py.sensor_message_processor import (
    SensorMessage,
    SensorMessageBuffer,
    SensorMessageProcessor,
)


@pytest.fixture
def test_buffer_and_processor():
    rclpy.init()
    test_node = Node('test_sensor_message_node')
    logger = test_node.get_logger()
    sensor_message_buffer = SensorMessageBuffer(logger, max_buffer_size=100)
    message_processor = SensorMessageProcessor(test_node, sensor_message_buffer)

    yield sensor_message_buffer, message_processor

    # shutdown the message processor to clean up the thread
    message_processor.shutdown()

    rclpy.shutdown()


@dataclass
class MessageProccessorTestParams:
    sensor_messages: list[SensorMessage]


@pytest.mark.parametrize(
    'test_parameters',
    [
        pytest.param(
            MessageProccessorTestParams(
                sensor_messages=[
                    SensorMessage(
                        name='cpu',
                        tags={'cpu': 'cpu0'},
                        fields={
                            'usage_active': 9.615384615386088,
                            'usage_system': 1.923076923076739,
                            'usage_user': 4.807692307693044,
                        },
                        timestamp=1756666979,
                    )
                ],
            ),
            id='incomplete_message',
        )
    ],
)
def test_buffer_complete_messages(
    test_buffer_and_processor: tuple[SensorMessageBuffer, SensorMessageProcessor],
    test_parameters: MessageProccessorTestParams,
):
    sensor_message_buffer, _ = test_buffer_and_processor
    for sensor_message in test_parameters.sensor_messages:
        sensor_message_buffer.add_message(json.dumps(asdict(sensor_message)))

    assert not sensor_message_buffer.is_empty()
