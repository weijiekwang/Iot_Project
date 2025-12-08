# oled_module.py
from machine import I2C, Pin
from config import OLED_WIDTH, OLED_HEIGHT, OLED_SCL_PIN, OLED_SDA_PIN
import ssd1306

class OledDisplay:
    def __init__(self):
        self.i2c = I2C(0, scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))
        self.oled = ssd1306.SSD1306_I2C(128, 32, self.i2c)
        self.clear()
        self.show_text("Smart Plant", "Booting...")

    def clear(self):
        self.oled.fill(0)
        self.oled.show()

    def show_text(self, line1="", line2=""):
        self.oled.fill(0)
        if line1:
            self.oled.text(line1, 0, 12, 1)
        if line2:
            self.oled.text(line2, 0, 24, 1)
        # if line3:
        #     self.oled.text(line3, 0, 32)
        self.oled.show()

    def show_large_text(self, line1="", line2=""):
        """
        Display two lines of text for horizontal 128x64 OLED.
        For 128x64 horizontal OLED:
        - Line 1 (time) at y=16 (upper half)
        - Line 2 (moisture) at y=40 (lower half)
        Centered horizontally for better visual balance.
        """
        self.oled.fill(0)

        # Line 1: Time display centered in upper half
        if line1:
            self.oled.text(line1, 0, 12, 1)
        if line2:
            self.oled.text(line2, 0, 24, 1)

        self.oled.show()
