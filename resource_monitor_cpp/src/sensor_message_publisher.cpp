

#include <cctype>
#include <map>
#include <memory>
#include <string>
#include <string_view>
#include <utility>

#include "rclcpp/node.hpp"
#include <builtin_interfaces/msg/time.hpp>
#include <rclcpp/time.hpp>

#include <fmt/format.h>

#include "resource_monitor_interfaces/msg/field.hpp"
#include "resource_monitor_interfaces/msg/resource.hpp"
#include "resource_monitor_cpp/sensor_message.hpp"
#include "resource_monitor_cpp/sensor_message_publisher.hpp"

using Field = resource_monitor_interfaces::msg::Field;
using TimeMsg = builtin_interfaces::msg::Time;
using TagsKey = std::map<std::string, std::string>;

SensorMessagePublisher::SensorMessagePublisher(const rclcpp::Node::SharedPtr& node,
                                               std::string_view sensor_type,
                                               const TagsKey& tag_keys)
  : node_{node}
  , logger_{node->get_logger()}
{
  std::string topic_name{create_topic_name(sensor_type, tag_keys)};

  publisher_ptr_ = node->create_publisher<ResourceType>(topic_name, 10);

  logger_.info("made resource publisher for {}", topic_name);
}

std::string SensorMessagePublisher::create_topic_name(std::string_view sensor_type,
                                                      const TagsKey& sensor_tags)
{
  if (sensor_tags.empty())
  {
    return std::string(sensor_type);
  }

  std::string topic_str{combine_type_and_tags(sensor_type, sensor_tags)};
  sanitize_topic_name(topic_str);
  return topic_str;
}

std::string SensorMessagePublisher::combine_type_and_tags(std::string_view sensor_type,
                                                          const TagsKey& sensor_tags)
{
  std::string topic_str{};

  bool first = true;
  for (const auto& [key, val] : sensor_tags)
  {
    if (!first)
    {
      topic_str.append("/");
    }
    topic_str.append(val);
    first = false;
  }
  return std::string(sensor_type) + "/" + topic_str;
}

void SensorMessagePublisher::sanitize_topic_name(std::string& topic_str)
{
  for (char& c : topic_str)
  {
    if (!std::isalnum(c) && c != '_' && c != '~' && c != '/')
    {
      c = '_';
    }
    c = static_cast<char>(std::tolower(c));
  }
}

void SensorMessagePublisher::publish(SensorMessage& message) const
{
  // use conversion operator to go from rclcpp::time to Time msg
  TimeMsg current_time{rclcpp::Time{message.timestamp}};

  // The message is built in a unique_ptr so it can be published by moving it. With
  // intra process communication enabled, publishing a unique_ptr hands ownership to the
  // intra process manager and subscribers in the same process read this exact instance.
  // refer to src/docs/intra_process_communication.md for more.
  auto resource = std::make_unique<ResourceType>();
  resource->header.stamp = current_time;

  for (const auto& [field_name, field_value] : message.fields)
  {
    Field field_msg{};
    field_msg.name = field_name;
    field_msg.value = field_value;

    resource->fields.emplace_back(std::move(field_msg));
  }

  // logging the address here and in the subscriber shows whether both ends touch the same
  // instance, which is the proof that intra process communication is actually being used
  logger_.debug("publishing message on {} at address {}", publisher_ptr_->get_topic_name(),
                fmt::ptr(resource.get()));

  publisher_ptr_->publish(std::move(resource));
}
