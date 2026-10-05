#pragma once

#include <map>
#include <string>
#include <thread>

#include "rclcpp/node.hpp"

#include <ros2_fmt_logger/logger.hpp>

#include "resource_monitor_cpp/sensor_message.hpp"
#include "resource_monitor_cpp/sensor_message_publisher.hpp"

using TagsKey = std::map<std::string, std::string>;
using PublisherMap = std::map<TagsKey, SensorMessagePublisher>;

class SensorMessageProcessor
{
private:
  const rclcpp::Node::SharedPtr node_;
  const ros2_fmt_logger::Logger logger_;

  std::map<std::string, PublisherMap> sensor_publishers_;
  SensorMessageBuffer& sensor_message_buffer_;

  std::thread publisher_thread_;

  void process_buffered_messages();
  const SensorMessagePublisher& get_publisher(const SensorMessage& message);

public:
  SensorMessageProcessor(const rclcpp::Node::SharedPtr& node,
                         SensorMessageBuffer& sensor_message_buffer);
  ~SensorMessageProcessor();
};
