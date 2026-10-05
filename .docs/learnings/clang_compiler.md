# Why the build command in `build.sh` looks like it does

When using the keyboard shortcut `ctrl+shift+b`, the build task is invoked from `tasks.json`. This
task runs the `.vscode/tasks/build.sh` script to build the ROS2 workspace. `.vscode/tasks/build.sh`
does not call `colcon build` with default options. This document explains each of those options,
and gives the measured effect of each one.

## The command in build.sh

The following shows the colcon build command that is used to build the ROS2 workspace.

```bash
colcon build \
    --symlink-install \
    --cmake-args \
    "-GNinja" \
    "-DCMAKE_MAKE_PROGRAM=/ros_ws/src/.vscode/tasks/ninja_on_stderr.sh" \
    "-DCMAKE_C_COMPILER=clang-21" \
    "-DCMAKE_CXX_COMPILER=clang++-21" \
    "-DCMAKE_C_FLAGS=-fdiagnostics-absolute-paths -fdiagnostics-color=always" \
    "-DCMAKE_CXX_FLAGS=-fdiagnostics-absolute-paths -fdiagnostics-color=always" \
    "-DCMAKE_EXPORT_COMPILE_COMMANDS=On"
    "$@"
```

## What each option measures

An experiment was run that added compiler options one at a time, starting from a plain
`colcon build --symlink-install`. Every value is the minimum of four passes. "Clean" is a full
build from an empty `build/`. "Rebuild" is a build after one `.cpp` file changed.

| Step | Option added                        | Clean build | Change  | Rebuild | Change  |
| ---- | ----------------------------------- | ----------- | ------- | ------- | ------- |
| 1    | (baseline)                          | 35.5 s      | —       | 3.23 s  | —       |
| 2    | `--parallel-workers 20`             | 36.1 s      | +0.6 s  | 3.20 s  | −0.03 s |
| 3    | `-GNinja`                           | 26.8 s      | −9.3 s  | 3.06 s  | −0.14 s |
| 4    | `-DCMAKE_BUILD_TYPE=RelWithDebInfo` | 34.9 s      | +8.1 s  | 3.64 s  | +0.58 s |
| 5    | clang 21 in place of GCC 11         | 21.5 s      | −13.4 s | 2.90 s  | −0.74 s |
| 6    | ccache, with an empty cache         | 22.9 s      | +1.4 s  | 3.05 s  | +0.15 s |
| 7    | ccache, with a filled cache         | 21.3 s      | −1.6 s  | 3.07 s  | +0.02 s |
| 8    | mold linker                         | 20.9 s      | −0.4 s  | 2.97 s  | −0.10 s |
| 9    | the full `build.sh`                 | 21.2 s      | +0.3 s  | 3.01 s  | +0.04 s |

The full command builds this workspace in about **21.5 s**. The plain command needs **35.5 s**.
That is 40 % less time. From this experiment I decided to keep the largest time savers, namely
Clang and Ninja.

### clang 21 in place of GCC 11 — 13.4 s less

This is the largest gain. It removes 38 % of the build time on its own. The `rclcpp` headers
contain a large amount of template code. GCC 11 spends most of its time in the optimiser on that
code. clang is faster at the same work.

`docker/Dockerfile` (dev stage) installs `clang-21` from apt.llvm.org, not from Ubuntu. The clang
that Ubuntu 22.04 ships cannot build this workspace. See
[Why clang 21](#why-clang-21-and-not-the-clang-that-ubuntu-2204-ships) below.

### `-GNinja` — 9.3 s less

This is the second largest gain. CMake writes Makefiles by default. Ninja starts faster and keeps
all cores busy better than `make` does. Nothing in the package `CMakeLists.txt` files needs a
change for it.

### `-DCMAKE_BUILD_TYPE=RelWithDebInfo` — 8.1 s more

This option makes the build **slower**. Without a build type, CMake gives the compiler no
optimisation flags at all. The result runs slowly. `RelWithDebInfo` turns on optimisation and still
keeps debug symbols, so a debugger and a stack trace still work. We accept 8 s of build time for
that, but will only use if we need to, so it is not a default.

## Why the rebuild time never moves

The rebuild column stays near 3 s at every step. Two numbers explain it:

- A rebuild with **no** change at all takes **1.43 s**. That is what colcon and CMake cost on every
  call. It is more than half of each rebuild time in the table. No compiler option can remove it.
  Only about 1.5 s of a rebuild is real work.
- A clean build compiles only 33 object files. The workspace is small.

## The options that are not about speed

These four options do not change the build time. The experiment measured them together as a last
step: they cost 0.3 s, which is inside the noise.

- `-DCMAKE_C_FLAGS` / `-DCMAKE_CXX_FLAGS` with `-fdiagnostics-absolute-paths` and
  `-fdiagnostics-color=always`. The first makes error messages give a full path, which the editor
  can open. The second keeps the colour, because ninja removes colour codes when it does not write
  to a terminal. `build.sh` also exports `CLICOLOR_FORCE=1` for the ninja side of the same problem.
- `-DCMAKE_EXPORT_COMPILE_COMMANDS=On` writes `compile_commands.json`. clangd in the editor needs
  that file in order to know where to look for code completetions.
- `-DCMAKE_MAKE_PROGRAM=.../ninja_on_stderr.sh` is a wrapper around ninja. It puts the output on
  stderr when the build fails. colcon only shows the stderr of a failed package, so compiler errors
  were invisible without it. Read the comment in that script for the detail.
- `--symlink-install` links files into `install/` in place of copying them. A change to a Python
  file or a launch file then needs no build at all.

## Why clang 21, and not the clang that Ubuntu 22.04 ships

Ubuntu 22.04 is the base of ROS Humble. It ships clang 14, and clang 15 is also in the archive.
Both fail on this workspace, for two separate reasons.

1. **`std::source_location` does not work.** Our `ros2_fmt_logger` dependency uses it. In
   libstdc++, `std::source_location` only works if the compiler gives it the
   `__builtin_source_location` builtin. GCC 11 has that builtin. clang got it in version 16. On
   clang 14 the header fails with `no type named 'source_location' in namespace 'std'`, and every
   logging call fails after it.

2. **The C++20 ranges headers fail.** Our code builds with `-std=gnu++20`. clang 14 and clang 15
   cannot compile the C++20 ranges and concepts headers of the libstdc++ 11 that Ubuntu 22.04
   ships. A `std::views::transform` call in `resource_diagnostics_updater_cpp` is rejected for this
   reason.

clang 16 and later fix both problems. apt.llvm.org gives recent clang builds for Ubuntu 22.04. In
August 2026 it offers clang 21 and clang 22. The `docker/Dockerfile` (dev stage) adds that
repository and installs `clang-21`.

---

## Sources

- [Build ROS 2 packages with GCC or Clang (gist by a ROS 2 maintainer)](https://gist.github.com/audrow/30c8c5cb1d2103614c1b674f640515ae)
- [Ubuntu bug #2038340: clang packages in 22.04 unusable out of the box](https://bugs.launchpad.net/bugs/2038340)
- [LLVM review D120159: implement `__builtin_source_location` in clang](https://reviews.llvm.org/D120159)
- [libstdc++ commit: tweak `source_location` for clang support](https://gcc.gnu.org/pipermail/libstdc++-cvs/2022q2/037681.html)
- [apt.llvm.org — LLVM packages for Ubuntu/Debian](https://apt.llvm.org/)
