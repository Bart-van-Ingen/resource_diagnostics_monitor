#include <chrono>
#include <cstddef>
#include <optional>
#include <thread>

#include <rclcpp/logger.hpp>

#include <gtest/gtest.h>

#include "resource_monitor_cpp/sensor_message.hpp"

TEST(SensorMessageBufferTest, ReturnsMessageWhenAvailable)
{
  SensorMessageBuffer buffer{rclcpp::get_logger("test_sensor_message_buffer"),
                             static_cast<std::size_t>(100)};

  // creates a new thread, capturing buffer by reference, and immediately starts running
  // the lambda body concurrently with the main test thread.
  std::thread producer([&buffer]() {
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    // R indicates raw string literal
    buffer.add_message(R"({"name":"cpu","tags":{},"fields":{},"timestamp":1})");
  });

  const std::optional<SensorMessage> message{buffer.get_message(std::chrono::milliseconds(500))};
  producer.join();

  ASSERT_TRUE(buffer.is_empty());
  ASSERT_TRUE(message.has_value());
  EXPECT_EQ(message->name, "cpu");
}

TEST(SensorMessageBufferTest, DropsMalformedMessage)
{
  SensorMessageBuffer buffer{rclcpp::get_logger("test_sensor_message_buffer"),
                             static_cast<std::size_t>(100)};

  buffer.add_message("not json");
  // valid json, but missing the fields a SensorMessage needs
  buffer.add_message(R"({"name":"cpu"})");

  EXPECT_FALSE(buffer.get_message(std::chrono::milliseconds(100)).has_value());
  EXPECT_FALSE(buffer.get_message(std::chrono::milliseconds(100)).has_value());
  ASSERT_TRUE(buffer.is_empty());
}

int main(int argc, char** argv)
{
  testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
