#pragma once

#include <chrono>
#include <condition_variable>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <optional>
#include <queue>
#include <string>
#include <unordered_map>

#include "rclcpp/logger.hpp"

#include <nlohmann/detail/macro_scope.hpp>
#include <nlohmann/json.hpp>
#include <nlohmann/json_fwd.hpp>
#include <ros2_fmt_logger/logger.hpp>

struct SensorMessage
{
  std::string name;
  std::unordered_map<std::string, std::string> tags;
  std::unordered_map<std::string, double> fields;
  int64_t timestamp;
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(SensorMessage, name, tags, fields, timestamp)

class SensorMessageBuffer
{
private:
  const ros2_fmt_logger::Logger logger_;
  const std::size_t max_buffer_size_{1};
  std::queue<std::string> buffer_{};

  std::mutex mutex_{};
  std::condition_variable condition_variable_{};

public:
  SensorMessageBuffer(const rclcpp::Logger& logger, const std::size_t max_buffer_size_);
  void add_message(std::string&& message);
  std::optional<SensorMessage> get_message(const std::chrono::milliseconds timeout);
  bool is_empty();
};
