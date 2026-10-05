#include <cerrno>
#include <chrono>
#include <cstring>
#include <iostream>
#include <string>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/un.h>
#include <thread>
#include <unistd.h>

#include <rclcpp/logger.hpp>
#include <rclcpp/utilities.hpp>

#include <gtest/gtest.h>

#include "resource_monitor_cpp/sensor_message.hpp"
#include "resource_monitor_cpp/unix_socket_manager.hpp"

class UnixSocketDummy
{
private:
  std::string socket_path_;
  int fd_{};
  sockaddr_un addr_{};

public:
  UnixSocketDummy(const std::string& socket_path)
    : socket_path_(socket_path)
  {
    fd_ = socket(AF_UNIX, SOCK_STREAM, 0);
    addr_.sun_family = AF_UNIX;
    std::strncpy(addr_.sun_path, socket_path_.c_str(), sizeof(addr_.sun_path) - 1);
  }
  void make_connection()
  {
    if (connect(fd_, reinterpret_cast<sockaddr*>(&addr_), sizeof(addr_)) == -1)
    {
      std::cout << "connect not possible: " << std::strerror(errno) << "\n";
      return;
    }
    if (write(fd_,
              R"({"name":"cpu","tags":{},"fields":{},"timestamp":1})"
              "\n",
              51) == -1)
    {
      std::cout << "write not possible"
                << "\n";
    }

    close(fd_);
  }
};

TEST(UnixSocketManagerTest, AcceptsConnectionWhenAvailable)
{
  std::string socket_path{"/tmp/dummy_socket.sock"};

  // creates a new thread, capturing buffer by reference, and immediately starts running
  // the lambda body concurrently with the main test thread.
  std::thread producer([&socket_path]() {
    UnixSocketDummy socket_dummy{socket_path};
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    socket_dummy.make_connection();
  });

  auto logger{rclcpp::get_logger("test_sensor_message_buffer")};
  logger.set_level(rclcpp::Logger::Level::Debug);
  SensorMessageBuffer buffer{logger, static_cast<std::size_t>(100)};
  {
    // socket_manager's destructor joins its read thread, which only returns once
    // the dummy client's message has been read and the connection has hit EOF
    // (the dummy closes its fd right after writing). Scoping it here lets us wait
    // deterministically instead of sleeping an arbitrary amount of time.
    UnixSocketManager socket_manager{logger, socket_path, buffer};
    producer.join();
  }

  ASSERT_TRUE(!buffer.is_empty());
}

int main(int argc, char** argv)
{
  testing::InitGoogleTest(&argc, argv);
  rclcpp::init(argc, argv);
  int result = RUN_ALL_TESTS();
  rclcpp::shutdown();
  return result;
}
