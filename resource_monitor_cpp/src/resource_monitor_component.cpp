#include <cstddef>
#include <memory>
#include <string>

#include "rclcpp_components/register_node_macro.hpp"
#include <rclcpp/node.hpp>
#include <rclcpp/node_interfaces/node_base_interface.hpp>
#include <rclcpp/node_options.hpp>

#include "resource_monitor_cpp/resource_monitor_component.hpp"

using NodeBaseInterfaceSharedPtrType = rclcpp::node_interfaces::NodeBaseInterface::SharedPtr;

ResourceMonitorNode::ResourceMonitorNode(const rclcpp::NodeOptions& options)
  : node_{std::make_shared<rclcpp::Node>("resource_monitor_node", options)}

  // declare_parameter returns the resolved value, so the members can be built from it directly
  , message_buffer_{node_->get_logger(),
                    static_cast<std::size_t>(node_->declare_parameter("max_buffer_size", 100))}

  , socket_manager_{node_->get_logger(),
                    node_->declare_parameter("socket_path", std::string{"/tmp/metric_collector.sock"}),
                    message_buffer_}

  , message_processor_{node_, message_buffer_}
{
}

NodeBaseInterfaceSharedPtrType ResourceMonitorNode::get_node_base_interface() const
{
  return node_->get_node_base_interface();
}

RCLCPP_COMPONENTS_REGISTER_NODE(ResourceMonitorNode)
