# Vendor Packages

## What a vendor package is

A vendor package is a normal ROS package whose only job is to provide some third-party software
that ROS needs, when that software is not available through the normal system package manager, or
when you need a specific version of it.

The clearest official definition comes from the Gazebo docs:

> "A ROS vendor package is a ROS package that provides software that ROS needs on platforms where
> it might not be available, or where a different version than what is available is required." —
> [Gazebo: ROS 2 Vendor Packages](https://gazebosim.org/docs/latest/ros2_gz_vendor_pkgs/)

In practice it does one of two things at build time:

- Downloads and builds a library from source, or
- Downloads a prebuilt binary (our telegraf case).

Then it installs the result into the workspace so the rest of your packages can use it.

## Why they exist

`rosdep` installs dependencies by looking up names in a public database and installing the matching
system package. That only works for software that is actually in the system repositories. When
something is not there — telegraf, a newer library version than Ubuntu ships, etc. — there is no
rosdep key to install. A vendor package fills that gap by fetching the software itself, while still
fitting into the standard workflow:

```bash
rosdep install --from-paths src --ignore-src -r -y
colcon build
```

`--ignore-src` tells rosdep "these packages are built from source, don't look for them in apt,"
which is why a `_vendor` package that isn't in the rosdep database doesn't cause an error.

## Where the convention is written down

There is **no single REP or spec** for vendor packages. It is a de-facto convention you learn by
reading existing ones. The official tooling (`ament_cmake_vendor_package`, which provides the
`ament_vendor()` CMake helper), REP 2005, and the existing `*_vendor` packages in the ROS 2 core
set together show the pattern is accepted, but none of them defines it.

## Best practices

Drawn from the reference packages and the ament docs:

1. **Naming.** Call it `<thing>_vendor`, lowercase with underscores. The `_vendor` suffix signals
   to everyone that it fetches third-party software.

2. **Build type `ament_cmake`.** Every vendor package in a standard Humble install uses CMake, not
   `ament_python` — because the work is "download a file at build time," which CMake does cleanly
   with `find_program`, `file(DOWNLOAD)` with checksum, and `install()`.

3. **Prefer an existing install.** Check for the software on the system first (`find_program` /
   `find_package`) and only download if it is missing. `uncrustify_vendor` does this. The
   `ament_vendor()` helper exposes it as the `SATISFIED` flag, and there is an
   `AMENT_VENDOR_POLICY` option for "never vendor" environments (used in `onnxruntime_vendor`).

4. **Pin the version and verify the download.** Hardcode the version and check the SHA256, so
   builds are reproducible and a corrupted or swapped file is caught.

5. **Install into the workspace, not the system.** Use relative `install()` destinations so
   everything lands under `install/<pkg>/`. No `sudo`, nothing written to system paths, and
   `rm -rf build install` fully removes it. Executables go in `bin` (so ament's PATH hook picks
   them up); libraries typically go under `opt/<pkg>/`.

6. **Handle multiple architectures.** Robots are often arm64, so pick the right download for
   `amd64` vs `arm64`.

7. **Let consumers depend on it normally.** Downstream packages add `<exec_depend>` (runtime) or
   `<depend>` (build + runtime) in their `package.xml`. That makes colcon build the vendor package
   first and makes the dependency visible to rosdep.

8. **Consider making the version overridable.** Exposing the version as a CMake cache variable lets
   others pick a different version at build time without forking the package.

## Why this repo does _not_ use `ament_vendor()`

`ament_cmake_vendor_package` (the `ament_vendor()` helper) is the official tool, and it _is_
available for Humble. We still hand-write plain CMake in `telegraf_vendor`, for three reasons
specific to telegraf: it expects a CMake project to build, telegraf ships as a prebuilt Go binary;
it installs under `opt/<pkg>/`, but the ament PATH hook only adds `bin/` to `PATH`; and we only
need download, unpack and install, which is a handful of plain CMake commands.

Rule of thumb: `ament_vendor()` shines when you are vendoring a **library built from source with
CMake**. For a **standalone prebuilt executable** like telegraf, plain CMake is shorter and puts
the binary exactly where it needs to be.


---

## Sources

- [Gazebo — ROS 2 Vendor Packages (definition)](https://gazebosim.org/docs/latest/ros2_gz_vendor_pkgs/)
- [ament_cmake documentation](https://docs.ros.org/en/rolling/How-To-Guides/Ament-CMake-Documentation.html)
