#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <stdio.h>
#include <string>
#include <sys/socket.h>
#include <sys/un.h>
#include <thread>
#include <unistd.h>

#include "rclcpp/logger.hpp"
#include "rclcpp/utilities.hpp"

#include "resource_monitor_cpp/sensor_message.hpp"
#include "resource_monitor_cpp/unix_socket_manager.hpp"

UnixSocketManager::UnixSocketManager(const rclcpp::Logger& logger,
                                     const std::string& socket_path,
                                     SensorMessageBuffer& sensor_message_buffer)
  : logger_{logger}
  , socket_path_{socket_path}
  , sensor_message_buffer_{sensor_message_buffer}
{
  create_socket();
  bind_socket();
  recieve_client_file_descriptor();

  read_thread_ = std::thread(&UnixSocketManager::read_data, this);
}

UnixSocketManager::~UnixSocketManager()
{
  // Wait for thread to finish
  if (read_thread_.joinable())
  {
    read_thread_.join();
  }
  // Remove the socket file so future runs can bind to the same path.
  if (unlink(socket_path_.c_str()) == -1)
  {
    logger_.warn("unlink({}) at shutdown failed: {}", socket_path_, std::strerror(errno));
  }

  logger_.info("UnixSocketManager exited");
}

void UnixSocketManager::create_socket()
{
  // Ensure any stale socket file is removed before binding. If unlink fails
  // for another reason than non-existence, that's non-fatal but logged.
  if (unlink(socket_path_.c_str()) == -1 && errno != ENOENT)
  {
    logger_.warn("unlink({}) failed: {}", socket_path_, std::strerror(errno));
  }

  // Create the listening UNIX domain socket.
  listen_fd_ = socket(AF_UNIX, SOCK_STREAM, 0);
  if (listen_fd_ == -1)
  {
    logger_.error("socket(AF_UNIX) failed: {}", std::strerror(errno));
  }
  logger_.info("created UNIX socket (listen_fd_= {})", listen_fd_);
}

void UnixSocketManager::bind_socket()
{
  sockaddr_un addr{};
  addr.sun_family = AF_UNIX;

  // make sure that we do not buffer overflow sun_path
  std::strncpy(addr.sun_path, socket_path_.c_str(), sizeof(addr.sun_path) - 1);

  // Bind the listening socket to the filesystem path.
  if (bind(listen_fd_, reinterpret_cast<const sockaddr*>(&addr), sizeof(addr)) == -1)
  {
    logger_.error("bind({}) failed: {}", socket_path_, std::strerror(errno));
    close(listen_fd_);
  }
  logger_.info("bound UNIX socket to {}", socket_path_);

  // Allow a small backlog; since we only accept a single client this value is not critical.
  if (listen(listen_fd_, 5) == -1)
  {
    logger_.error("listen() failed: {}", std::strerror(errno));
    close(listen_fd_);
    unlink(socket_path_.c_str());
  }
  logger_.info("listening for a single client on {}", socket_path_);
}

void UnixSocketManager::recieve_client_file_descriptor()
{
  // Accept exactly one client connection. This call will block until a client
  // connects or an error occurs.
  client_fd_ = accept(listen_fd_, nullptr, nullptr);
  if (client_fd_ == -1)
  {
    logger_.error("accept() failed: {}", std::strerror(errno));
    close(listen_fd_);
    unlink(socket_path_.c_str());
  }
  logger_.info("accepted client (client_fd_={}). closing listening socket", client_fd_);

  // Close the listening socket we don't need to accept more clients.
  close(listen_fd_);
}

void UnixSocketManager::read_data()
{
  // Use FILE* and getline for convenient line-oriented reads from the socket.
  // fdopen() creates a stream wrapper around the client_fd_. We must ensure
  // that fclose() is called to release resources and close the underlying fd.
  FILE* socket_file{fdopen(client_fd_, "r")};
  if (!socket_file)
  {
    logger_.error("fdopen(client_fd_={}) failed: {}", client_fd_, std::strerror(errno));
    close(client_fd_);
    unlink(socket_path_.c_str());
    return;
  }

  logger_.info("Unix socket connected to {}. Starting read thread", client_fd_);

  // getline will allocate/rescale `lineptr` as needed. We free it after use.
  char* lineptr{nullptr};
  size_t linecap{0};
  ssize_t linelen;

  // Read lines from the stream until EOF. getline() returns the number of bytes read
  // and stores the line in lineptr, resizing the buffer as needed
  while (rclcpp::ok() && (linelen = getline(&lineptr, &linecap, socket_file)) != -1)
  {
    // Strip trailing newline for cleaner logs and downstream processing.
    if (linelen > 0 && lineptr[linelen - 1] == '\n')
    {
      lineptr[linelen - 1] = '\0';
    }
    // More informative log including the number of bytes read and the content.
    logger_.debug("received {} bytes: {}", linelen, lineptr);
    sensor_message_buffer_.add_message(static_cast<std::string>(lineptr));
  }

  // Clean up allocated buffer and close the FILE* (which also closes client_fd_).
  free(lineptr);
  fclose(socket_file);
}
