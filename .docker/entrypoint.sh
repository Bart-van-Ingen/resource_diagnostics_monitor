#!/bin/bash
# Basic entrypoint for ROS / Colcon Docker containers
# Source ROS 2
source /opt/ros/${ROS_DISTRO}/setup.bash
echo "Sourced ROS 2 ${ROS_DISTRO}"

# Activate Python virtual environment AFTER ROS setup
# This ensures venv python takes priority in PATH for correct shebangs
source /ros_ws/.venv/bin/activate
echo "Activated venv at .venv"

# If the workspace exists, source the workspace
if [ -d "/ros_ws" ]; then
    source /ros_ws/install/setup.bash
    echo "Sourced workspace at /ros_ws"
fi

# CRITICAL: Add venv site-packages to PYTHONPATH so ROS 2 nodes can find
# packages installed in the virtual environment. The ROS 2 setup scripts
# override PYTHONPATH and don't include venv packages automatically.
# See: https://robotics.stackexchange.com/questions/98214/how-to-use-python-virtual-environments-with-ros2
export PYTHONPATH="/ros_ws/.venv/lib/python3.10/site-packages:${PYTHONPATH}"
echo "Added venv site-packages to PYTHONPATH"

# `history -a` appends new lines immediately; `history -n` reads back lines other shells have
# appended, so Ctrl-R sees them without a restart.
# Only meaningful in the interactive shells that source this file via .bashrc; harmless
# when this script runs as the container ENTRYPOINT.
PROMPT_COMMAND='history -a; history -n'

# Execute the command passed into this entrypoint
exec "$@"
