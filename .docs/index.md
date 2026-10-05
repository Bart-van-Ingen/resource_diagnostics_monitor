# Resource Diagnostics Monitor

<p align="center">
   <img src="images/resource-monitor-lizard-logo.png" alt="Resource Monitor Lizard Logo" width="50%" />
</p>

This site contains the detailed documentation of the
[Resource Diagnostics Monitor](https://github.com/Bart-van-Ingen/resource_diagnostics_monitor). This
repository provides a ROS 2-based resource monitoring solution that leverages a metric collector (Telegraf or Collectd) to collect
system metrics and publish them as ROS messages, with the possibility of also plugging into ROS2
diagnostics.  
Everything needed to run the package without knowing all the details can be found on the repo
readme, so head on over there if you are in a hurry, I won't hold it against you.

For the rest of you, this documentation contains two things:

- The motivation and architecture of this package.
- Things I learned along the way that supplement ros2 documentation.
