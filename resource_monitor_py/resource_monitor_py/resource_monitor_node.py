import contextlib
import traceback

import rclpy
from rclpy._rclpy_pybind11 import RCLError  # ty: ignore[unresolved-import]
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from resource_monitor_py.sensor_message import SensorMessageBuffer
from resource_monitor_py.sensor_message_processor import SensorMessageProcessor
from resource_monitor_py.unix_socket_manager import UnixSocketManager


def main(args=None):
    rclpy.init(args=args)
    node = Node('resource_monitor_node')
    logger = node.get_logger()

    node.declare_parameter('max_buffer_size', 100)
    max_buffer_size = node.get_parameter('max_buffer_size').get_parameter_value().integer_value

    node.declare_parameter('socket_path', '/tmp/metric_collector.sock')
    socket_path = node.get_parameter('socket_path').get_parameter_value().string_value

    sensor_message_buffer = SensorMessageBuffer(logger, max_buffer_size)
    unix_socket_manager = UnixSocketManager(logger, sensor_message_buffer, socket_path)
    sensor_message_processor = SensorMessageProcessor(node, sensor_message_buffer)

    try:
        rclpy.spin(node)

    except (KeyboardInterrupt, ExternalShutdownException):
        logger.info('system_monitor_node received valid kill signal')

    except Exception:
        logger.error(traceback.format_exc())
        raise

    finally:
        sensor_message_processor.shutdown()
        unix_socket_manager.shutdown()
        node.destroy_node()
        with contextlib.suppress(RCLError):
            rclpy.shutdown()


if __name__ == '__main__':
    main()
