#pragma once

#include <cstdint>
#include <string>

#include "globals.h"
#include "plugin.h"

namespace utils
{
uint64_t cdtime_to_ns(cdtime_t t);

std::string create_field_name(const value_list_t& value_list, const data_source_t& data_source);

std::string suffixed(const std::string& name, const char* type, const char* suffix);
}  // namespace utils
