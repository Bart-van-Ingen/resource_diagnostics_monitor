#include <chrono>
#include <optional>
#include <string>
#include <thread>
#include <utility>

#include "rclcpp/node.hpp"
#include "rclcpp/utilities.hpp"

#include <ros2_fmt_logger/logger.hpp>

#include "resource_monitor_cpp/sensor_message.hpp"
#include "resource_monitor_cpp/sensor_message_processor.hpp"
#include "resource_monitor_cpp/sensor_message_publisher.hpp"

using namespace std::chrono_literals;

SensorMessageProcessor::SensorMessageProcessor(const rclcpp::Node::SharedPtr& node,
                                               SensorMessageBuffer& sensor_message_buffer)
  : node_{node}
  , logger_{node_->get_logger()}
  , sensor_message_buffer_{sensor_message_buffer}
{
  publisher_thread_ = std::thread(&SensorMessageProcessor::process_buffered_messages, this);
}

SensorMessageProcessor::~SensorMessageProcessor()
{
  if (publisher_thread_.joinable())
  {
    publisher_thread_.join();
  }
}

void SensorMessageProcessor::process_buffered_messages()
{
  while (rclcpp::ok())
  {
    // Wait up to 100ms for the next buffered sensor message; if none arrives,
    // retry. Note that std::optional has a usage syntax that is essentially identical to a pointer,
    // but is not a pointer.
    std::optional<SensorMessage> message = sensor_message_buffer_.get_message(100ms);
    if (!message)
    {
      continue;
    }

    const SensorMessagePublisher& publisher = get_publisher(*message);
    publisher.publish(*message);
  }
}

const SensorMessagePublisher& SensorMessageProcessor::get_publisher(const SensorMessage& message)
{
  const std::string sensor_type{message.name};

  // order the keys consistently using the map instead of the unordered map
  const TagsKey tags_key{message.tags.begin(), message.tags.end()};

  // The [] operator on std::map will default-construct a new entry if
  // the key doesn't exist.
  PublisherMap& sensor_type_publishers{sensor_publishers_[sensor_type]};

  // find returns an itterator that will point to a pair contain the key and publisher
  auto key_publisher_pair = sensor_type_publishers.find(tags_key);
  if (key_publisher_pair == sensor_type_publishers.end())
  {
    // move semantics will occur on emplace of temporary SensorMessagePublisher.
    // emplace returns a pair, where the first is the itterator.
    key_publisher_pair = sensor_type_publishers
                             .emplace(tags_key,
                                      SensorMessagePublisher(node_, sensor_type, tags_key))
                             .first;
  }
  // second is the SensorMessagePublisher we found or constructed above in the map
  return key_publisher_pair->second;
}
