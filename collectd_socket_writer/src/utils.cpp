#include <cstdint>
#include <cstring>
#include <string>

#include "collectd_socket_writer/utils.hpp"
#include "globals.h"
#include "plugin.h"

namespace utils
{
// copied from "utils_time.h" to supress "compound literals are a c99-specific feature"
uint64_t cdtime_to_ns(cdtime_t t)
{
  return ((t >> 30) * 1000000000) + (((t & 0x3fffffff) * 1000000000 + (1 << 29)) >> 30);
}

// collectd splits one logical measurement over several dispatches, one per type and
// type_instance (the cpu states, the disk counters, ...). Those dispatches share a series
// key, so both have to go into the field name to keep the values apart inside one message.
std::string create_field_name(const value_list_t& value_list, const data_source_t& data_source)
{
  std::string name{value_list.type_instance};

  // single valued types call their only data source "value", which adds nothing next to
  // the type that follows it
  if (std::strcmp(data_source.name, "value") != 0)
  {
    if (!name.empty())
    {
      name += "_";
    }
    name += data_source.name;
  }

  // the type says what the value measures, so it names the field rather than the topic
  if (!name.empty())
  {
    name += "_";
  }
  name += value_list.type;

  return name;
}

// collectd names some of its types after the data source type itself, as with the "gauge"
// and "derive" types, which would repeat it in the field name. The suffix is left off there.
std::string suffixed(const std::string& name, const char* type, const char* suffix)
{
  if (std::strcmp(type, suffix) == 0)
  {
    return name;
  }
  return name + "_" + suffix;
}

}  // namespace utils
