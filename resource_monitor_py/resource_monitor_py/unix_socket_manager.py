import contextlib
import socket
import threading
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

        # Accepted client connection, kept so that shutdown can unblock the blocking read
        self.conn: socket.socket | None = None

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

        if self.conn is not None:
            with contextlib.suppress(OSError):
                self.conn.shutdown(socket.SHUT_RDWR)

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
        self.conn = conn
        if not self.should_continue_loop():
            conn.close()
            return

        try:
            # makefile gives line-oriented reads from the socket, like getline in the C++
            # version. The socket must be blocking: a timeout can corrupt the file buffer.
            conn.settimeout(None)
            with conn, conn.makefile('r', encoding='utf-8') as socket_file:
                for line in socket_file:
                    if not self.should_continue_loop():
                        break

                    message = line.removesuffix('\n')
                    self.logger.debug(f'received line: {message}')
                    self.sensor_message_buffer.add_message(message)

        except (OSError, UnicodeDecodeError) as e:
            self.logger.error(f'Error handling connection: {e}')
