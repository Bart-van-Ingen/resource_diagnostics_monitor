# Intra-Process Communication

## Overview

### What it is

Two nodes in the same process, ie in a [composable node](composable_nodes.md), can pass a message
directly. The message stays in memory. It does not go to the DDS middleware. It is not serialized.
It does not go through the network stack. This is intra-process communication.

The result is lower latency and less CPU load. If one node sends the message and no other node
needs its own version, there is no copy at all. The reader gets the same message that the writer
made.

### How this repo does it

Three conditions must be true. All three are true in this repo.

1. **Both nodes run in one process.** The composed launch file loads the resource monitor and the
   diagnostics updater into one container. This is the only way the two nodes can share memory.
2. **Both nodes have the setting turned on.** The composed launch file turns the setting on for
   each of the two nodes.
3. **The publisher hands over the message.** The resource monitor makes the message and gives it
   away. It keeps no copy of its own. Because of this, the framework does not have to make a copy
   for the reader.

The subscriber side needs no change. The diagnostics updater asks for a message it can only read.
Several readers can therefore share one message.

### When it is off

The setting is off by default. It is also off in two normal situations:

- You start the two nodes as separate processes, with `ros2 run` or with the single-node launch
  file.
- Another process subscribes to the same topic, for example `ros2 topic echo`.

In all of these cases the messages go through DDS, as they always did. Nothing breaks. The code is
the same. Only the transport is slower.

The last case is a mix. The reader in the same process still gets the fast path. The reader in the
other process gets a DDS copy at the same time.

This mixed case is common. It happens each time you look at a topic with `ros2 topic echo` while
the container runs. Our subscriber is built for it. The subscriber asks only to read the message.
It does not ask to own it. Because of this, the framework can give the same message to the reader
in the process and to DDS.


### Limits to know

- One setting is not enough. If only one of the two nodes has it, the messages go through DDS.
- The QoS settings must fit. The history must keep the last N messages, the depth must not be zero,
  and the durability must be volatile. This repo meets all three. If it did not, the node would
  stop at start-up with a clear error.

## The bare minimum

This is all the code you need to get intra process communication working.

### 1. Turn the setting on for both nodes

Do this in the launch file, once per node in the container. This is what
[resource_diagnostics_monitor_cpp_launch.py](https://github.com/Bart-van-Ingen/resource_diagnostics_monitor/blob/main/resource_diagnostics_monitor_bringup/launch/resource_diagnostics_monitor_cpp_launch.py)
does.

```python
(
    ComposableNode(
        package='my_package',
        plugin='MyNode',
        name='my_node',
        extra_arguments=[{'use_intra_process_comms': True}],
    ),
)
```

### 2. Give the message away in the publisher

Make the message in a `unique_ptr`. Move it into `publish`. By doing this move semantics are invoked. Move semantics means the class will transfer ownership of the object rather than making a copy of the object when calling the publish function.

```cpp
auto msg = std::make_unique<MyMessage>();
msg->data = 42;

publisher_->publish(std::move(msg));
```

### 3. Ask only to read in the subscriber

Take the message as a `ConstSharedPtr`. Here we are getting a pointer to the message instead of a copy of the message in the lambda function subscription callback. We can then dereference the pointer and get access to the original object that was published, with no copying involved.

```cpp
subscription_ = node.create_subscription<MyMessage>(
    "my_topic", 10,
    [this](const MyMessage::ConstSharedPtr& msg) { use_message(*msg); });
...

void MyObject::use_message(const MyMessage& resource)
{
}
```

## Sources

- [Concept: Composition][1]
- [How-to guide: Launch composable nodes][14]
- [Demo: Intra-process communication][2]

[1]: https://docs.ros.org/en/humble/Concepts/Intermediate/About-Composition.html
[2]: https://docs.ros.org/en/humble/Tutorials/Demos/Intra-Process-Communication.html
[14]: https://docs.ros.org/en/humble/How-To-Guides/Launching-composable-nodes.html
