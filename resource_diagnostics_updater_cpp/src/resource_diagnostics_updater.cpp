
#include <algorithm>
#include <utility>

#include "rclcpp/node.hpp"
#include <diagnostic_msgs/msg/detail/key_value__struct.hpp>
#include <rclcpp/message_info.hpp>

#include <fmt/core.h>
#include <fmt/format.h>
#include <ros2_fmt_logger/logger.hpp>

#include "resource_diagnostics_updater_cpp/diagnosed_resource.hpp"
#include "resource_diagnostics_updater_cpp/diagnostic_publisher.hpp"
#include "resource_diagnostics_updater_cpp/resource_diagnostics_updater.hpp"
#include "resource_monitor_interfaces/msg/resource.hpp"

using ResourceType = resource_monitor_interfaces::msg::Resource;
using KeyValueType = diagnostic_msgs::msg::KeyValue;

ResourceDiagnosticsUpdater::ResourceDiagnosticsUpdater(rclcpp::Node& node,
                                                       DiagnosticPublisher& diagnostic_publisher,
                                                       DiagnosedResource&& diagnosed_resource)
  : diagnostic_publisher_{diagnostic_publisher}
  , diagnosed_resource_(std::move(diagnosed_resource))
  , logger_{node.get_logger()}
{
  diagnostic_status_.level = DiagnosticStatusType::STALE;
  diagnostic_status_.name = diagnosed_resource_.name;
  diagnostic_status_.message = "unknown";
  diagnostic_status_.hardware_id = "resource_diagnostics_monitor";

  diagnostic_publisher_.add_diagnostic_status(diagnostic_status_);

  subscription_ = node.create_subscription<ResourceType>(
      diagnosed_resource_.topic, 1,
      [this](const ResourceType::ConstSharedPtr& resource, const rclcpp::MessageInfo& info) {
        // the address matches the one the publisher logged when the message came through the
        // intra process manager. a different address means it was copied by the middleware
        logger_.debug("received message at address {} from {}", fmt::ptr(resource.get()),
                      info.get_rmw_message_info().from_intra_process ? "intra process" :
                                                                       "the middleware");
        resource_callback(*resource);
      });

  logger_.info("resource diagnostic updater initiated for {} in {} on topic {}",
               diagnosed_resource_.name, diagnosed_resource_.field, diagnosed_resource_.topic);
}

void ResourceDiagnosticsUpdater::resource_callback(const ResourceType& resource)
{
  // find returns as an itterator which uses pointer notation
  auto find = std::find_if(
      resource.fields.begin(), resource.fields.end(),
      [this](const auto& field) { return field.name == diagnosed_resource_.field; });

  if (find != resource.fields.end())
  {
    logger_.debug("found target field {} with value {}", find->name, find->value);
  }
  else
  {
    logger_.warn("cannot find {}", diagnosed_resource_.field);
    return;
  }

  KeyValueType key_value{};
  key_value.key = find->name;
  key_value.value = fmt::format("{}", find->value);

  diagnostic_status_.values = {std::move(key_value)};

  if (find->value >= diagnosed_resource_.error_threshold)
  {
    diagnostic_status_.level = DiagnosticStatusType::ERROR;
    diagnostic_status_.message = fmt::format("error for {} ({}): {} over error threshold {}",
                                             diagnosed_resource_.name, diagnosed_resource_.field,
                                             find->value, diagnosed_resource_.error_threshold);
  }
  else if (find->value >= diagnosed_resource_.warning_threshold)
  {
    diagnostic_status_.level = DiagnosticStatusType::WARN;
    diagnostic_status_.message = fmt::format("warning for {} ({}): {} over warning threshold {}",
                                             diagnosed_resource_.name, diagnosed_resource_.field,
                                             find->value, diagnosed_resource_.warning_threshold);
  }
  else
  {
    diagnostic_status_.level = DiagnosticStatusType::OK;
    diagnostic_status_.message = fmt::format("{} ok", diagnosed_resource_.name);
    return;
  }
  // immediately publish if at warn or error level
  diagnostic_publisher_.publish_diagnostics({diagnostic_status_});
}