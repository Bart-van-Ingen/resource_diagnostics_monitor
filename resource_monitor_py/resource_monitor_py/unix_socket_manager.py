import socket
import threading
from json import JSONDecodeError
from pathlib import Path
from threading import Thread

from rclpy.impl.rcutils_logger import RcutilsLogger

from resource_monitor_py.sensor_message import SensorMessageBuffer


class UnixSocketManager:
    def __init__(
        self,
        logger: RcutilsLogger,
        sensor_message_buffer: SensorMessageBuffer,
        socket_path: str,
    ) -> None:

        self.logger = logger
        self.sensor_message_buffer = sensor_message_buffer

        # Add shutdown flag so that we can shutdown in unit testing
        self.shutdown_event = threading.Event()

        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket_path = Path(socket_path)
        logger.info(f'server listening on {self.socket_path}')

        # Remove existing socket file if it exists
        if self.socket_path.exists():
            self.socket_path.unlink()

        # Bind and listen in a separate thread
        self.listener_thread = Thread(target=self.start_socket_listener)
        logger.info('starting unix socket listener thread...')
        self.listener_thread.start()

    def shutdown(self) -> None:
        self.shutdown_event.set()

        # Close the socket to unblock any waiting operations
        try:
            self.server_socket.close()
            self.logger.info('unix socket closed.')
        except OSError as e:
            self.logger.warning(f'Error closing socket: {e}')

        # Remove existing socket file if it exists
        if self.socket_path.exists():
            self.socket_path.unlink()

        # Only join if we're not calling from the same thread
        current_thread = threading.current_thread()
        if self.listener_thread.is_alive() and self.listener_thread != current_thread:
            self.listener_thread.join(timeout=1.0)  # Wait max 1 second

    def start_socket_listener(self) -> None:
        try:
            self.server_socket.bind(str(self.socket_path))
            self.server_socket.listen()
            self.server_socket.settimeout(0.1)

            while self.should_continue_loop():
                result = self.handle_socket_operation(self.server_socket.accept)

                if result is None:  # timeout
                    continue

                elif not result:
                    break

                received_data: tuple[socket.socket, str] = result

                conn, addr = received_data

                self.logger.debug(f'connected by {addr}')

                self.handle_connection(conn)

        except OSError as e:
            self.logger.error(f'Error in socket listener: {e}')

        finally:
            self.logger.debug('Socket listener thread exiting')

    def should_continue_loop(self) -> bool:
        """Check if the main loop should continue running."""
        return not self.shutdown_event.is_set()

    def handle_socket_operation(self, operation_func, *args, **kwargs):
        """Handle socket operations with common timeout and error handling."""
        try:
            return operation_func(*args, **kwargs)

        except TimeoutError:
            # Timeout allows us to check shutdown_event periodically
            return None

        except OSError:
            return False

    def handle_connection(self, conn: socket.socket) -> None:
        """Handle a single client connection."""
        message_buffer = ''

        try:
            with conn:
                conn.settimeout(0.1)

                while self.should_continue_loop():
                    result = self.handle_socket_operation(conn.recv, 1024)

                    if result is None:  # timeout
                        continue

                    elif not result:
                        break

                    received_data: bytes = result

                    decoded_message = received_data.decode('utf-8')

                    message_buffer = self.buffer_complete_messages(
                        decoded_message,
                        message_buffer,
                        self.sensor_message_buffer,
                    )

        except (OSError, UnicodeDecodeError, JSONDecodeError, TypeError) as e:
            self.logger.error(f'Error handling connection: {e}')

    @staticmethod
    def buffer_complete_messages(
        decoded_message: str,
        message_buffer: str,
        sensor_message_buffer: SensorMessageBuffer,
    ) -> str:

        message_lines = decoded_message.split('\n')

        # Process all complete entries (all but the last split part)
        if len(message_lines) > 1:
            # Add the first part to our current entry and process it
            message_buffer += message_lines[0]
            sensor_message_buffer.add_message(message_buffer)
            message_buffer = ''

            # Process any additional complete entries
            for complete_line in message_lines[1:-1]:
                sensor_message_buffer.add_message(complete_line)

                # Keep the last part (which may be incomplete) for the next iteration
        message_buffer += message_lines[-1]

        return message_buffer
