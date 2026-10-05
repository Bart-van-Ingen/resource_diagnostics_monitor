#pragma once

#include "rclcpp/node.hpp"
#include "rclcpp/node_options.hpp"
#include <rclcpp/node_interfaces/node_base_interface.hpp>

#include "resource_monitor_cpp/sensor_message.hpp"
#include "resource_monitor_cpp/sensor_message_processor.hpp"
#include "resource_monitor_cpp/unix_socket_manager.hpp"

using NodeBaseInterfaceSharedPtrType = rclcpp::node_interfaces::NodeBaseInterface::SharedPtr;

// Composable node. Exposes get_node_base_interface(), which is all rclcpp_components needs to load
// it into a container.
class ResourceMonitorNode
{
private:
  rclcpp::Node::SharedPtr node_;

  // declaration order is construction order in the initializer list of the constructor.
  // the buffer must exist before the two classes below it that hold a reference to it
  SensorMessageBuffer message_buffer_;
  UnixSocketManager socket_manager_;
  SensorMessageProcessor message_processor_;

public:
  explicit ResourceMonitorNode(const rclcpp::NodeOptions& options);

  NodeBaseInterfaceSharedPtrType get_node_base_interface() const;
};
