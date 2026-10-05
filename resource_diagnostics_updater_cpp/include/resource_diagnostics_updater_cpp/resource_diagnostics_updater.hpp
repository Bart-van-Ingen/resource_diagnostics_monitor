
#include <diagnostic_msgs/msg/diagnostic_status.hpp>
#include <rclcpp/node.hpp>
#include <rclcpp/subscription.hpp>

#include <ros2_fmt_logger/logger.hpp>

#include "resource_diagnostics_updater_cpp/diagnosed_resource.hpp"
#include "resource_diagnostics_updater_cpp/diagnostic_publisher.hpp"
#include "resource_monitor_interfaces/msg/resource.hpp"

using DiagnosticStatusType = diagnostic_msgs::msg::DiagnosticStatus;
using ResourceType = resource_monitor_interfaces::msg::Resource;

class ResourceDiagnosticsUpdater
{
private:
  DiagnosticPublisher& diagnostic_publisher_;
  DiagnosedResource diagnosed_resource_;
  const ros2_fmt_logger::Logger logger_;
  DiagnosticStatusType diagnostic_status_{};

  rclcpp::Subscription<ResourceType>::SharedPtr subscription_{};

  void resource_callback(const ResourceType& resource);

public:
  ResourceDiagnosticsUpdater(rclcpp::Node& node,
                             DiagnosticPublisher& diagnostic_publisher,
                             DiagnosedResource&& diagnosed_resource);
};