# moisture_sensor_module.py
from machine import Pin, ADC
import time

class MoistureSensor:
    """
    Moisture sensor reader for capacitive soil moisture sensor
    Connected to GPIO39 (ADC1) - AOUT pin
    """

    def __init__(self, pin=39):
        """
        Initialize the moisture sensor

        Args:
            pin: GPIO pin number (default: 39, which is ADC1)
        """
        self.adc = ADC(Pin(pin))
        # Set ADC attenuation to read full 0-3.3V range
        self.adc.atten(ADC.ATTN_11DB)
        # Set ADC width to 12-bit (0-4095)
        self.adc.width(ADC.WIDTH_12BIT)

        # Calibration values (adjust based on your sensor)
        self.dry_value = 4095  # Value when completely dry (in air)
        self.wet_value = 0     # Value when completely wet (in water)

        print("Moisture sensor initialized on GPIO{}".format(pin))

    def read_raw(self):
        """
        Read raw ADC value

        Returns:
            int: Raw ADC value (0-4095)
        """
        return self.adc.read()

    def read_voltage(self):
        """
        Read sensor voltage

        Returns:
            float: Voltage in volts (0-3.3V)
        """
        raw = self.read_raw()
        return (raw / 4095.0) * 3.3

    def read_moisture_percent(self):
        """
        Read moisture level as percentage

        Returns:
            float: Moisture percentage (0-100%)
                   0% = completely dry
                   100% = completely wet
        """
        raw = self.read_raw()
        # Invert the reading (sensor reads HIGH when dry, LOW when wet)
        moisture = 100 - (raw / 4095.0 * 100)
        # Clamp to 0-100 range
        return max(0, min(100, moisture))

    def get_status(self):
        """
        Get moisture status as a string

        Returns:
            str: Status description (Dry/Low/Medium/High/Wet)
        """
        moisture = self.read_moisture_percent()

        if moisture < 20:
            return "Dry"
        elif moisture < 40:
            return "Low"
        elif moisture < 60:
            return "Medium"
        elif moisture < 80:
            return "High"
        else:
            return "Wet"

    def calibrate(self, dry_seconds=5, wet_seconds=5):
        """
        Calibrate the sensor by measuring dry and wet values

        Args:
            dry_seconds: Seconds to measure in air (dry)
            wet_seconds: Seconds to measure in water (wet)
        """
        print("\nCalibration starting...")
        print("Place sensor in AIR and wait...")
        time.sleep(2)

        # Measure dry value
        dry_readings = []
        for i in range(dry_seconds):
            dry_readings.append(self.read_raw())
            print("  Dry reading {}: {}".format(i+1, dry_readings[-1]))
            time.sleep(1)

        self.dry_value = sum(dry_readings) // len(dry_readings)
        print("Dry value calibrated: {}".format(self.dry_value))

        print("\nNow place sensor in WATER and wait...")
        time.sleep(3)

        # Measure wet value
        wet_readings = []
        for i in range(wet_seconds):
            wet_readings.append(self.read_raw())
            print("  Wet reading {}: {}".format(i+1, wet_readings[-1]))
            time.sleep(1)

        self.wet_value = sum(wet_readings) // len(wet_readings)
        print("Wet value calibrated: {}".format(self.wet_value))
        print("\nCalibration complete!")
        print("Dry: {}, Wet: {}".format(self.dry_value, self.wet_value))

    def read_all(self):
        """
        Read all sensor data at once

        Returns:
            dict: Dictionary with raw, voltage, percent, and status
        """
        raw = self.read_raw()
        voltage = (raw / 4095.0) * 3.3
        percent = 100 - (raw / 4095.0 * 100)
        percent = max(0, min(100, percent))

        if percent < 20:
            status = "Dry"
        elif percent < 40:
            status = "Low"
        elif percent < 60:
            status = "Medium"
        elif percent < 80:
            status = "High"
        else:
            status = "Wet"

        return {
            "raw": raw,
            "voltage": voltage,
            "moisture_percent": percent,
            "status": status
        }
