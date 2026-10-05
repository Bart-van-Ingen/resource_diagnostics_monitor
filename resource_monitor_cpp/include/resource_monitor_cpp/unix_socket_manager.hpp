#pragma once

#include <string>
#include <thread>

#include "rclcpp/logger.hpp"

#include <ros2_fmt_logger/logger.hpp>

#include "sensor_message.hpp"

class UnixSocketManager
{
private:
  const ros2_fmt_logger::Logger logger_;
  const std::string socket_path_;
  SensorMessageBuffer& sensor_message_buffer_;

  std::thread read_thread_;  // read thread

  int listen_fd_ = -1;  // file descriptor for the listening socket
  int client_fd_ = -1;  // file descriptor for the accepted client connection

  void create_socket();
  void bind_socket();
  void recieve_client_file_descriptor();

  void read_data();

public:
  UnixSocketManager(const rclcpp::Logger& logger,
                    const std::string& socket_path,
                    SensorMessageBuffer& sensor_message_buffer);

  ~UnixSocketManager();

  const std::string get_socket_path()
  {
    return socket_path_;
  }
};
