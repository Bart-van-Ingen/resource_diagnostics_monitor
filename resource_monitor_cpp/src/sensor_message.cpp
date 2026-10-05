#include <chrono>
#include <cstddef>
#include <mutex>
#include <optional>
#include <string>
#include <utility>

#include "rclcpp/logger.hpp"

#include <nlohmann/json_fwd.hpp>

#include "resource_monitor_cpp/sensor_message.hpp"

using json = nlohmann::json;

SensorMessageBuffer::SensorMessageBuffer(const rclcpp::Logger& logger,
                                         const std::size_t max_buffer_size)
  : logger_{logger}
  , max_buffer_size_{max_buffer_size} {};

// we use a r value reference so that we can move it into the buffer without needing to copy
void SensorMessageBuffer::add_message(std::string&& message)
{
  {
    std::lock_guard<std::mutex> lock{mutex_};
    while (buffer_.size() >= max_buffer_size_)
    {
      logger_.warn("buffer contains {} messages and is full, dropping oldest message",
                   buffer_.size());
      buffer_.pop();
    }

    buffer_.push(std::move(message));
  }
  condition_variable_.notify_one();
}

std::optional<SensorMessage>
SensorMessageBuffer::get_message(const std::chrono::milliseconds timeout)
{
  std::string message{};
  {
    std::unique_lock<std::mutex> lock{mutex_};

    if (!condition_variable_.wait_for(lock, timeout, [this] { return !buffer_.empty(); }))
    {
      return std::nullopt;
    }

    message = std::move(buffer_.front());
    buffer_.pop();
  }

  // A malformed line, or one missing a field, would throw and terminate the processor thread,
  // so it is dropped instead. json::exception covers both the parse_error from parse() and the
  // type_error or out_of_range from get<SensorMessage>().
  try
  {
    // Must use '=' not '{}': brace-init would invoke json's initializer_list
    // constructor, wrapping the parsed object in a 1-element array.
    // https://json.nlohmann.me/home/faq/#brace-initialization-yields-arrays
    json parsed_data = json::parse(message.begin(), message.end());
    return parsed_data.get<SensorMessage>();
  }
  catch (const json::exception& e)
  {
    logger_.warn("dropping message that could not be parsed: {} ({})", e.what(), message);
    return std::nullopt;
  }
}

bool SensorMessageBuffer::is_empty()
{
  std::lock_guard<std::mutex> lock{mutex_};
  return buffer_.empty();
}
