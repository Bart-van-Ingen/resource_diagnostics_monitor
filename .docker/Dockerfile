# ROS distribution to use
ARG ROS_DISTRO=humble

#####################
# Base Image #
#####################
FROM osrf/ros:${ROS_DISTRO}-desktop AS base
ENV ROS_DISTRO=${ROS_DISTRO}
SHELL ["/bin/bash", "-c"]

# Install all apt packages in one layer and clean up cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget socat jq lm-sensors \
    && rm -rf /var/lib/apt/lists/*

# Install uv - fast Python package installer and resolver
# https://docs.astral.sh/uv/, https://docs.astral.sh/uv/guides/integration/docker/ 
# Install to /usr/local/bin so it's available to all users (including devcontainer user)
ENV UV_INSTALL_DIR="/usr/local/bin"
# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh
# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Install Telegraf
RUN wget https://dl.influxdata.com/telegraf/releases/telegraf-1.35.3_linux_amd64.tar.gz \
    && tar -xzf telegraf-1.35.3_linux_amd64.tar.gz \
    && rm telegraf-1.35.3_linux_amd64.tar.gz \
    && mv telegraf-1.35.3/usr/bin/telegraf /usr/local/bin/telegraf \
    && chmod +x /usr/local/bin/telegraf

#####################
# Overlay Image #
#####################
FROM base AS overlay

# Create an overlay Colcon workspace
RUN mkdir -p /ros_ws/src
WORKDIR /ros_ws
COPY . ./src/

# install dependencies
## rosdep
RUN source /opt/ros/${ROS_DISTRO}/setup.bash \
    && apt-get update -y \
    && rosdep install -y --from-paths src --ignore-src --rosdistro ${ROS_DISTRO}

## uv
ENV UV_PROJECT_ENVIRONMENT=/ros_ws/.venv
ENV VIRTUAL_ENV=/ros_ws/.venv
ENV PATH="/ros_ws/.venv/bin:$PATH"
# Copy rather than hardlink: the uv cache mount is on a different filesystem.
ENV UV_LINK_MODE=copy

# COLCON_IGNORE keeps `colcon build` from walking the venv, which it would otherwise
# do since it discovers packages from the cwd.
RUN uv venv --system-site-packages /ros_ws/.venv \
    && touch /ros_ws/.venv/COLCON_IGNORE
RUN --mount=type=cache,target=/root/.cache/uv uv sync --project src

# build workspace 
RUN source /opt/ros/${ROS_DISTRO}/setup.bash\
    && source .venv/bin/activate\
    && python3 -m colcon build\
    --symlink-install \
    --cmake-args \
    "-DCMAKE_EXPORT_COMPILE_COMMANDS=On" \
    && rm -rf /var/lib/apt/lists/*

# Remove display warnings
RUN mkdir /tmp/runtime-root
ENV XDG_RUNTIME_DIR=/tmp/runtime-root
RUN chmod -R 0700 /tmp/runtime-root
ENV NO_AT_BRIDGE=1

# Set up the entrypoint
COPY ./.docker/entrypoint.sh /
ENTRYPOINT [ "/entrypoint.sh" ]

#####################
# Development Image #
#####################
FROM overlay AS dev

# Add ninja for quicker cpp compiling times.
RUN apt-get update && apt-get install -y ninja-build

# Add clang 21 from apt.llvm.org. build.sh compiles with it. See docs/clang_compiler.md.
RUN wget -qO- https://apt.llvm.org/llvm-snapshot.gpg.key > /etc/apt/trusted.gpg.d/apt.llvm.org.asc \
    && echo "deb http://apt.llvm.org/jammy/ llvm-toolchain-jammy-21 main" > /etc/apt/sources.list.d/llvm21.list \
    && apt-get update \
    && apt-get install -y clang-21 \
    && rm -rf /var/lib/apt/lists/*

# Add dev user with same UID and GID as your host system
# (copied from https://code.visualstudio.com/remote/advancedcontainers/add-nonroot-user#_creating-a-nonroot-user)
ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && rm -rf /var/lib/apt/lists/*

# Set the ownership of the overlay workspace to the new user
RUN chown -R dev:dev /ros_ws

# Set the ownership of the XDG_RUNTIME_DIR to the new user for vscode
RUN chown -R dev:dev /tmp/runtime-root

# Add SSH keys for github SSH git actions
RUN mkdir -p /home/$USERNAME/.ssh
RUN ssh-keyscan github.com >> /home/$USERNAME/.ssh/known_hosts
RUN chown -R $USERNAME:$USERNAME /home/$USERNAME/.ssh

# install dependencies for documentation
RUN --mount=type=cache,target=/root/.cache/uv uv sync --project src --group docs

# Switch from root to user
USER $USERNAME

# source our ROS environment not just at container startup, but every time we attach a new
# interactive shell while our dev container remains up.
RUN echo "source /entrypoint.sh" >> /home/${USERNAME}/.bashrc
