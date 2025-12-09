from machine import Pin
import time

# GPIO pin wiring
PUMP_PIN = 25
ON_TIME_SECONDS = 1
OFF_INTERVAL_SECONDS = 5


class WaterPump:
    def __init__(self, pin: int):
        # Default to OFF on startup
        self.pump = Pin(pin, Pin.OUT)
        self.turn_off()
        print(f"[Water Pump] Initialized on GPIO{pin} (default OFF)")

    def turn_on(self):
        self.pump.value(1)
        print("[Water Pump] ON - Watering...")

    def turn_off(self):
        self.pump.value(0)
        print("[Water Pump] OFF - Stopped")

    def pulse(self, duration_sec: int):
        print(f"[Water Pump] Pulse for {duration_sec} second(s)")
        self.turn_on()
        time.sleep(duration_sec)
        self.turn_off()


def test_pump():
    print("=" * 50)
    print("Water Pump Pulse Test")
    print("=" * 50)
    print(f"Pump control pin: GPIO{PUMP_PIN}")
    print(f"Cycle: ON for {ON_TIME_SECONDS}s, then OFF for {OFF_INTERVAL_SECONDS}s")
    print("Press Ctrl+C to stop\n")

    pump = WaterPump(PUMP_PIN)

    try:
        while True:
            pump.pulse(ON_TIME_SECONDS)
            print(f"Waiting {OFF_INTERVAL_SECONDS} second(s) before next pulse...")
            time.sleep(OFF_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n[Test] Interrupted by user (Ctrl+C)")
    finally:
        pump.turn_off()
        print("[Test] Water pump turned OFF")
        print("[Test] Program exited")


if __name__ == "__main__":
    test_pump()

