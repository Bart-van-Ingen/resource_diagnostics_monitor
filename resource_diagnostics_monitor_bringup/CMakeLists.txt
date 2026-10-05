cmake_minimum_required(VERSION 3.8)
project(resource_diagnostics_monitor_bringup)

# This package has no compiled targets, so the workspace's
# -DCMAKE_EXPORT_COMPILE_COMMANDS flag has nothing to attach to. Read it here
# so CMake doesn't warn that it went unused.
if(CMAKE_EXPORT_COMPILE_COMMANDS)
endif()


find_package(ament_cmake REQUIRED)

install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
