cmake_minimum_required(VERSION 3.8)
project(collectd_socket_writer)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(collectd_vendor REQUIRED)
find_package(fmt REQUIRED)
find_package(nlohmann_json REQUIRED)


# collectd loads "<PluginDir>/<name>.so", so no "lib" prefix.
add_library(collectd_socket_writer MODULE
  src/collectd_socket_writer.cpp
  src/socket_writer.cpp
  src/utils.cpp
)
# Hide all symbols by default. Only module_register is exported.
set_target_properties(collectd_socket_writer PROPERTIES
  PREFIX ""
  CXX_VISIBILITY_PRESET hidden
  VISIBILITY_INLINES_HIDDEN ON
)
target_include_directories(collectd_socket_writer PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/include
  ${collectd_vendor_INCLUDE_DIRS})
target_compile_definitions(collectd_socket_writer PRIVATE ${collectd_vendor_DEFINITIONS})
target_compile_features(collectd_socket_writer PRIVATE cxx_std_20)
target_link_libraries(collectd_socket_writer PRIVATE fmt::fmt nlohmann_json::nlohmann_json
)

install(TARGETS collectd_socket_writer
  LIBRARY DESTINATION lib/collectd
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  # the following line skips uncrustify, which enforces the ROS style and
  # disagrees with src/.clang-format on brace placement and pointer
  # alignment. clang-format is the single source of truth for this repo.
  set(ament_cmake_uncrustify_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
