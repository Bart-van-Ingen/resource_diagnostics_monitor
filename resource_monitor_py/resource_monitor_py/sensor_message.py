import json
import threading
from collections import deque
from dataclasses import dataclass

from rclpy.impl.rcutils_logger import RcutilsLogger


@dataclass
class SensorMessage:
    name: str
    tags: dict
    fields: dict
    timestamp: int

    @staticmethod
    def from_json_str(json_str: str) -> 'SensorMessage':
        sensor_dict = json.loads(json_str)
        return SensorMessage(**sensor_dict)


class SensorMessageBuffer:
    def __init__(self, logger: RcutilsLogger, max_buffer_size: int) -> None:
        self.logger = logger
        self.max_buffer_size = max_buffer_size
        self.buffer: deque[str] = deque()
        self.condition = threading.Condition()

    def add_message(self, message: str) -> None:
        self.logger.debug(f'adding message to buffer: {message}')
        with self.condition:
            while len(self.buffer) >= self.max_buffer_size:
                self.logger.warning(
                    f'buffer contains {len(self.buffer)} messages and is full, '
                    'dropping oldest message'
                )
                self.buffer.popleft()

            self.buffer.append(message)
            self.condition.notify()

    def get_message(self, timeout: float = 0.1) -> SensorMessage | None:
        self.logger.debug('getting message from buffer...')
        with self.condition:
            if not self.condition.wait_for(lambda: self.buffer, timeout=timeout):
                return None

            message = self.buffer.popleft()

        # A malformed line, or one with missing or extra keys, would raise and stop the
        # processor thread, so it is dropped instead. JSONDecodeError comes from json.loads,
        # TypeError from SensorMessage(**sensor_dict).
        try:
            return SensorMessage.from_json_str(message)
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.warning(f'dropping message that could not be parsed: {e} ({message})')
            return None

    def is_empty(self) -> bool:
        with self.condition:
            return not self.buffer
