#include <cstring>

#include "collectd_socket_writer/socket_writer.hpp"
#include "plugin.h"

static SocketWriter socket_writer;

extern "C" {

static const char* config_keys[] = {"SocketPath"};
static int config_keys_num = sizeof(config_keys) / sizeof(config_keys[0]);

static int sw_config(const char* key, const char* value)
{
  if (strcmp(key, "SocketPath") == 0)
  {
    socket_writer.set_socket_path(value);
  }
  return 0;
}

static int sw_init()
{
  return socket_writer.init();
}

static int sw_write(const data_set_t* ds, const value_list_t* vl, user_data_t* ud)
{
  (void)ud;
  return socket_writer.write(ds, vl);
}

static int sw_shutdown()
{
  return socket_writer.shutdown();
}

__attribute__((visibility("default"))) void module_register(void)
{
  plugin_register_config("collectd_socket_writer", sw_config, config_keys, config_keys_num);
  plugin_register_init("collectd_socket_writer", sw_init);
  plugin_register_write("collectd_socket_writer", sw_write, nullptr);
  plugin_register_shutdown("collectd_socket_writer", sw_shutdown);
}

}  // extern "C"
