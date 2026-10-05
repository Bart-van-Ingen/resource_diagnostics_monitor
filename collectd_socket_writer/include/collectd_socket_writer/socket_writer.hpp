#pragma once
extern "C" {
#include "plugin.h"
}

#include <cstdint>
#include <map>
#include <mutex>
#include <string>
#include <sys/un.h>
#include <unordered_map>
#include <utility>

using PluginKey = std::pair<const std::string, const std::string>;
using MeasurementFields = std::unordered_map<std::string, double>;

struct PluginDataSet
{
  std::string name;
  uint64_t timestamp;
  std::unordered_map<std::string, std::string> tags{};
  std::unordered_map<std::string, double> fields{};
};

class SocketWriter
{
public:
  int init();
  int write(const data_set_t* ds, const value_list_t* vl);
  int shutdown();
  void set_socket_path(std::string path)
  {
    socket_path_ = std::move(path);
  };

private:
  int server_fd_{};  // file descriptor for the accepted server connection
  sockaddr_un addr_{};

  std::mutex mutex_{};
  std::string socket_path_{};
  bool connected_{false};
  bool connect_socket();

  // one entry per series, holding the values gathered so far for the current cycle
  std::map<PluginKey, PluginDataSet> pending_plugin_datasets_{};

  void set_dataset_plugin_instance(const value_list_t& value_list, PluginDataSet& data_set_struct);
  PluginDataSet create_plugin_dataset(const value_list_t& value_list);
  MeasurementFields create_measurement_fields(const data_set_t& data_set,
                                              const value_list_t& value_list);
  void send_plugin_dataset(const PluginDataSet& data_set_struct);

  void send_data_on_cycle_end(const MeasurementFields& measurement_fields,
                              PluginDataSet& plugin_dataset);
};
