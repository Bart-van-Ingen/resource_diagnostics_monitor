
#include <algorithm>
#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <string>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <unordered_map>

#include <fmt/core.h>
#include <nlohmann/detail/macro_scope.hpp>
#include <nlohmann/json.hpp>
#include <nlohmann/json_fwd.hpp>

#include "collectd_socket_writer/socket_writer.hpp"
#include "collectd_socket_writer/utils.hpp"
#include "plugin.h"

using json = nlohmann::json;
using MeasurementFields = std::unordered_map<std::string, double>;

// we add the following to generate the to_json functions for the struct automagically
NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(PluginDataSet, name, timestamp, tags, fields);

int SocketWriter::init()
{
  INFO("collectd_socket_writer: socket path set to %s", socket_path_.c_str());
  server_fd_ = socket(AF_UNIX, SOCK_STREAM, 0);
  addr_.sun_family = AF_UNIX;
  std::strncpy(addr_.sun_path, socket_path_.c_str(), sizeof(addr_.sun_path) - 1);

  return 0;
}

int SocketWriter::write(const data_set_t* data_set_ptr, const value_list_t* value_list_ptr)
{
  if (!connect_socket())
  {
    return 1;
  }

  const value_list_t& value_list{*value_list_ptr};
  const data_set_t& data_set{*data_set_ptr}

  DEBUG("collectd_socket_writer: write %s/%s-%s/%s (%zu values)", value_list.host,
        value_list.plugin, value_list.plugin_instance, value_list.type, data_set.ds_num);

  MeasurementFields measurement_fields{create_measurement_fields(data_set, value_list)};

  const PluginKey plugin_key{value_list.plugin, value_list.plugin_instance};

  std::lock_guard<std::mutex> lock(mutex_);

  // get the existing set or make an empty entry for it in the unordered map
  PluginDataSet& pending_plugin_dataset = pending_plugin_datasets_[plugin_key];

  send_data_on_cycle_end(measurement_fields, pending_plugin_dataset);

  // an empty batch is either the entry we just default constructed when using the plugin key or the
  // one we just sent on cycle end, so the identity and the timestamp are taken from the value that
  // opens the new cycle
  if (pending_plugin_dataset.fields.empty())
  {
    pending_plugin_dataset = create_plugin_dataset(value_list);
  }

  pending_plugin_dataset.fields.merge(measurement_fields);
  return 0;
}

bool SocketWriter::connect_socket()
{
  if (connected_)
  {
    return true;
  }

  std::lock_guard<std::mutex> lock(mutex_);

  if (connect(server_fd_, reinterpret_cast<sockaddr*>(&addr_), sizeof(addr_)) == -1)
  {
    WARNING("collectd_socket_writer: connect not possible: %s", std::strerror(errno));
    return false;
  }

  connected_ = true;
  return true;
}

MeasurementFields SocketWriter::create_measurement_fields(const data_set_t& data_set,
                                                          const value_list_t& value_list)
{
  MeasurementFields fields{};

  for (size_t i = 0; i < data_set.ds_num; ++i)
  {
    value_u value{value_list.values[i]};
    std::string name{utils::create_field_name(value_list, data_set.ds[i])};

    switch (data_set.ds[i].type)
    {
      case DS_TYPE_GAUGE:
        fields.emplace(utils::suffixed(name, value_list.type, "gauge"), value.gauge);
        break;
      case DS_TYPE_COUNTER:
        fields.emplace(utils::suffixed(name, value_list.type, "counter"), value.counter);
        break;
      case DS_TYPE_DERIVE:
        fields.emplace(utils::suffixed(name, value_list.type, "derive"), value.derive);
        break;
      case DS_TYPE_ABSOLUTE:
        fields.emplace(utils::suffixed(name, value_list.type, "absolute"), value.absolute);
        break;
    }
  }
  return fields;
}

void SocketWriter::send_data_on_cycle_end(const MeasurementFields& measurement_fields,
                                          PluginDataSet& plugin_dataset)
{
  // A data set never reports the same measurement field twice in one read cycle, so a field we
  // already hold means collectd has moved on to the next cycle and the batch is complete and can
  // be sent.

  const bool next_cycle{std::any_of(measurement_fields.begin(), measurement_fields.end(),
                                    [&plugin_dataset](const auto& field) {
                                      return plugin_dataset.fields.count(field.first) != 0;
                                    })};

  if (next_cycle)
  {
    send_plugin_dataset(plugin_dataset);
    plugin_dataset.fields.clear();
  }
}

void SocketWriter::send_plugin_dataset(const PluginDataSet& data_set_struct)
{
  // convert from struct to json using  implicit converting constructor. Cannot use brace init since
  // it would create a json array
  json data_set_json = data_set_struct;
  const std::string json_dump{data_set_json.dump() + "\n"};
  DEBUG("collectd_socket_writer: %s ", json_dump.c_str());

  if (::write(server_fd_, json_dump.c_str(), json_dump.size()) == -1)
  {
    connected_ = false;
  }
}

PluginDataSet SocketWriter::create_plugin_dataset(const value_list_t& value_list)
{
  // we take the time of the earliest measurement and use that to stamp the set
  PluginDataSet data_set_struct{value_list.plugin, utils::cdtime_to_ns(value_list.time)};

  set_dataset_plugin_instance(value_list, data_set_struct);
  return data_set_struct;
}

void SocketWriter::set_dataset_plugin_instance(const value_list_t& value_list,
                                               PluginDataSet& data_set_struct)
{
  if (value_list.plugin_instance[0] != '\0')
  {
    // if small than 3 characters it is likely a number, which cannot be used in a topic name
    // directly so we prefix it with the plugin name.
    if (strlen(value_list.plugin_instance) < 3)
    {
      data_set_struct.tags.emplace(
          "instance", fmt::format("{}_{}", value_list.plugin, value_list.plugin_instance));
    }
    else
    {
      data_set_struct.tags.emplace("instance", value_list.plugin_instance);
    }
  }
}

int SocketWriter::shutdown()
{
  // the batch of the last read cycle is still pending, so it goes out before we stop
  {
    std::lock_guard<std::mutex> lock(mutex_);
    if (connected_)
    {
      for (const auto& entry : pending_plugin_datasets_)
      {
        if (!entry.second.fields.empty())
        {
          send_plugin_dataset(entry.second);
        }
      }
    }
    pending_plugin_datasets_.clear();
  }

  INFO("collectd_socket_writer: shutdown, fd %d", server_fd_);
  return 0;
}
