cmake_minimum_required(VERSION 3.8)
project(resource_monitor_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic -Wconversion)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(resource_monitor_interfaces REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(ros2_fmt_logger REQUIRED)

# Everything except the node's main() builds once into this library. The node
# and every test link it rather than recompiling the same sources, so each file
# gets a single entry in compile_commands.json. Without this, clang-tidy sees
# one entry per target and analyses the same file once for each of them.
file(GLOB_RECURSE RESOURCE_MONITOR_SOURCES CONFIGURE_DEPENDS
  src/*.cpp
  include/*.hpp)
# the component source is excluded here because it builds into the shared component
# library below. the plugin registration in it must live in that shared library
list(REMOVE_ITEM RESOURCE_MONITOR_SOURCES ${CMAKE_CURRENT_SOURCE_DIR}/src/resource_monitor_component.cpp)

add_library(resource_monitor_lib STATIC ${RESOURCE_MONITOR_SOURCES})
target_include_directories(resource_monitor_lib PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_compile_features(resource_monitor_lib PUBLIC c_std_99 cxx_std_17)  # Require C99 and C++17
ament_target_dependencies(
  resource_monitor_lib
  "rclcpp"
  "resource_monitor_interfaces"
)

# Link the third-party JSON library
target_link_libraries(
resource_monitor_lib
nlohmann_json::nlohmann_json
ros2_fmt_logger::ros2_fmt_logger)

# Parsing the rclcpp header tree dominates compile time for every file here,
# so build it once as a precompiled header and share it across targets.
target_precompile_headers(resource_monitor_lib PRIVATE
  <rclcpp/rclcpp.hpp>)

# the static lib is linked into the shared component library, so it must be
# compiled as position independent code
set_target_properties(resource_monitor_lib PROPERTIES POSITION_INDEPENDENT_CODE ON)

# The composable node. Loading it into a component container needs a shared library.
add_library(resource_monitor_component SHARED src/resource_monitor_component.cpp)
target_link_libraries(resource_monitor_component resource_monitor_lib)
ament_target_dependencies(resource_monitor_component "rclcpp_components")
target_precompile_headers(resource_monitor_component REUSE_FROM resource_monitor_lib)

# This also generates and installs the resource_monitor_node executable,
# so "ros2 run" as a separate process keeps working
rclcpp_components_register_node(resource_monitor_component
  PLUGIN "ResourceMonitorNode"
  EXECUTABLE resource_monitor_node)

install(TARGETS resource_monitor_component
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

# Add the launch files
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  find_package(ament_cmake_gtest REQUIRED)
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

  file(GLOB TEST_SOURCES CONFIGURE_DEPENDS test/test_*.cpp)

  foreach(TEST_SOURCE ${TEST_SOURCES})
    # NAME_WE stands for "Name Without Extension"
    get_filename_component(TEST_NAME ${TEST_SOURCE} NAME_WE)

    ament_add_gtest(${TEST_NAME} ${TEST_SOURCE})

    # Include dirs, rclcpp, JSON and the logger all propagate from the library.
    target_link_libraries(${TEST_NAME} resource_monitor_lib)
    # the tests cannot reuse the library's precompiled header anymore: the library is
    # built with -fPIC (needed for the shared component library) while test
    # executables are built as PIE, and clang rejects a precompiled header whose
    # PIC/PIE flags differ. so each test builds its own.
    target_precompile_headers(${TEST_NAME} PRIVATE <rclcpp/rclcpp.hpp>)
  endforeach()

endif()

ament_package()
