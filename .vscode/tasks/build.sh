#!/bin/bash
set -e

# Keep compiler colors: ninja strips ANSI codes when it is not writing to a
# terminal, unless CLICOLOR_FORCE is set. The compiler side is forced by
# -fdiagnostics-color below.
export CLICOLOR_FORCE=1

# Build from the colcon workspace root regardless of where this was invoked from
cd /ros_ws

# Compile with clang 21 from apt.llvm.org instead of GCC: see docs/clang_compiler.md for the 
# research behind this choice. That page also says why ccache and mold were
# measured and then dropped again.
# CMAKE_MAKE_PROGRAM points at a wrapper that puts ninja's output on stderr
# when it fails, so colcon's default error display shows compiler errors.
# See the comment in ninja_on_stderr.sh.
colcon build \
    --symlink-install \
    --cmake-args \
    "-GNinja" \
    "-DCMAKE_MAKE_PROGRAM=/ros_ws/src/.vscode/tasks/ninja_on_stderr.sh" \
    "-DCMAKE_C_COMPILER=clang-21" \
    "-DCMAKE_CXX_COMPILER=clang++-21" \
    "-DCMAKE_C_FLAGS=-fdiagnostics-absolute-paths -fdiagnostics-color=always" \
    "-DCMAKE_CXX_FLAGS=-fdiagnostics-absolute-paths -fdiagnostics-color=always" \
    "-DCMAKE_EXPORT_COMPILE_COMMANDS=On" \
    "-DCMAKE_BUILD_TYPE=${BUILD_TYPE:-RelWithDebInfo}" \
    "$@" # Allows you to pass extra args like --packages-select from the CLI
