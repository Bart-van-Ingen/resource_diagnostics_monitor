# based on: https://github.com/ros/resource_retriever/blob/humble/libcurl_vendor/CMakeLists.txt
# libcurl_vendor is the only autotools vendor package in ROS, so it is the closest match. The
# staging install block comes from uncrustify_vendor and zstd_vendor. This file deviates from them
# in three places: "make -j" instead of "$(MAKE)", a DESTDIR staged install, and no system check.
cmake_minimum_required(VERSION 3.14)

project(collectd_vendor)

find_package(ament_cmake REQUIRED)

# This package has no compiled targets, so the workspace's
# -DCMAKE_EXPORT_COMPILE_COMMANDS flag has nothing to attach to. Read it here
# so CMake doesn't warn that it went unused.
if(CMAKE_EXPORT_COMPILE_COMMANDS)
endif()

# Avoid DOWNLOAD_EXTRACT_TIMESTAMP warning for CMake >= 3.24
if (POLICY CMP0135)
  cmake_policy(SET CMP0135 NEW)
endif()

macro(build_collectd)
  include(ExternalProject)
  ExternalProject_Add(collectd-5.12.0
    URL https://github.com/collectd/collectd/releases/download/collectd-5.12.0/collectd-5.12.0.tar.bz2
    URL_HASH SHA256=5bae043042c19c31f77eb8464e56a01a5454e0b39fa07cf7ad0f1bfc9c3a09d6
    CONFIGURE_COMMAND
      <SOURCE_DIR>/configure
      # collectd bakes these paths into the daemon, so unlike the other vendor
      # packages it must be configured with the final prefix, not the build
      # folder. DESTDIR below stages the files without changing the paths.
      --prefix=${CMAKE_INSTALL_PREFIX}
      # collectd installs the daemon in sbin, but the ament hook only puts bin on PATH.
      --sbindir=${CMAKE_INSTALL_PREFIX}/bin
      # Start from nothing and add back every plugin that needs no external
      # library on Linux. The user can then turn them on in the config file
      # without a rebuild. The default (all plugins on) is not used, because
      # then the plugin set depends on which -dev packages are installed.
      --disable-all-plugins
      --enable-aggregation
      --enable-apcups
      --enable-battery
      --enable-buddyinfo
      --enable-cgroups
      --enable-check_uptime
      --enable-chrony
      --enable-conntrack
      --enable-contextswitch
      --enable-cpu
      --enable-cpufreq
      --enable-cpusleep
      --enable-csv
      --enable-df
      --enable-disk
      --enable-drbd
      --enable-email
      --enable-entropy
      --enable-ethstat
      --enable-exec
      --enable-fhcount
      --enable-filecount
      --enable-fscache
      --enable-hddtemp
      --enable-hugepages
      --enable-infiniband
      --enable-interface
      --enable-ipc
      --enable-ipvs
      --enable-irq
      --enable-load
      --enable-logfile
      --enable-logparser
      --enable-madwifi
      --enable-match_empty_counter
      --enable-match_hashed
      --enable-match_regex
      --enable-match_timediff
      --enable-match_value
      --enable-mbmon
      --enable-mcelog
      --enable-md
      --enable-mdevents
      --enable-memcached
      --enable-memory
      --enable-multimeter
      --enable-network
      --enable-nfs
      --enable-notify_nagios
      --enable-ntpd
      --enable-numa
      --enable-olsrd
      --enable-openvpn
      --enable-pcie_errors
      --enable-powerdns
      --enable-processes
      --enable-protocols
      --enable-serial
      --enable-statsd
      --enable-swap
      --enable-synproxy
      --enable-syslog
      --enable-table
      --enable-tail
      --enable-tail_csv
      --enable-target_notification
      --enable-target_replace
      --enable-target_scale
      --enable-target_set
      --enable-target_v5upgrade
      --enable-tcpconns
      --enable-teamspeak2
      --enable-ted
      --enable-thermal
      --enable-threshold
      --enable-turbostat
      --enable-ubi
      --enable-unixsock
      --enable-uptime
      --enable-users
      --enable-uuid
      --enable-vmem
      --enable-vserver
      --enable-wireless
      --enable-write_graphite
      --enable-write_influxdb_udp
      --enable-write_log
      --enable-write_sensu
      --enable-write_syslog
      --enable-write_tsdb
      --enable-zfs_arc
      --enable-zookeeper
      # These bindings are built even when their plugins are off. Java needs a
      # JDK, Perl installs modules into the install space and wants YAML::Any.
      --without-java
      --without-perl-bindings
      # collectd builds with -Werror by default, which turns any warning from a
      # newer compiler into a build failure.
      --disable-werror
    # libcurl_vendor uses "$(MAKE)" here, but that is a Makefile variable and
    # Ninja rejects it as a bad $-escape. build.sh builds with -GNinja.
    BUILD_COMMAND make -j
    INSTALL_COMMAND make install DESTDIR=${CMAKE_CURRENT_BINARY_DIR}/collectd_install
    TIMEOUT 600
  )

  # The external project will install to the build folder, but we'll install that on make install.
  install(
    DIRECTORY
      ${CMAKE_CURRENT_BINARY_DIR}/collectd_install${CMAKE_INSTALL_PREFIX}/
    DESTINATION
      ${CMAKE_INSTALL_PREFIX}
    USE_SOURCE_PERMISSIONS
  )

  # "make install" only installs the libcollectdclient headers, not the headers
  # a plugin needs. Install plugin.h and the headers it includes, and keep the
  # source layout because they include each other with paths like
  # "liboconfig/oconfig.h". config.h is generated by configure in the build folder.
  ExternalProject_Get_Property(collectd-5.12.0 SOURCE_DIR BINARY_DIR)
  set(COLLECTD_PLUGIN_INCLUDE_DIR include/collectd/core)
  install(
    FILES
      ${SOURCE_DIR}/src/daemon/collectd.h
      ${SOURCE_DIR}/src/daemon/configfile.h
      ${SOURCE_DIR}/src/daemon/globals.h
      ${SOURCE_DIR}/src/daemon/plugin.h
      ${SOURCE_DIR}/src/daemon/utils_time.h
    DESTINATION ${COLLECTD_PLUGIN_INCLUDE_DIR}/daemon
  )
  install(
    FILES ${SOURCE_DIR}/src/liboconfig/oconfig.h
    DESTINATION ${COLLECTD_PLUGIN_INCLUDE_DIR}/liboconfig
  )
  install(
    FILES ${SOURCE_DIR}/src/utils/metadata/meta_data.h
    DESTINATION ${COLLECTD_PLUGIN_INCLUDE_DIR}/utils/metadata
  )
  install(
    FILES ${BINARY_DIR}/src/config.h
    DESTINATION ${COLLECTD_PLUGIN_INCLUDE_DIR}
  )
endmacro()

# Unlike the other vendor packages there is no system check here. A collectd on
# the system is built with an unknown plugin set, and the fixed plugin set above
# is the reason this package exists.
build_collectd()

# Both folders are needed: plugin.h includes "configfile.h" from its own folder
# and "utils/metadata/meta_data.h" from the parent. collectd.h only includes
# config.h when HAVE_CONFIG_H is set, and collectd builds its own plugins with it.
ament_export_include_directories(
  ${COLLECTD_PLUGIN_INCLUDE_DIR}
  ${COLLECTD_PLUGIN_INCLUDE_DIR}/daemon
)
ament_export_definitions(HAVE_CONFIG_H=1)

ament_package()
