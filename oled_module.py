# oled_module.py
from machine import I2C, Pin
from config import OLED_WIDTH, OLED_HEIGHT, OLED_SCL_PIN, OLED_SDA_PIN
import ssd1306

class OledDisplay:
    def __init__(self):
        self.i2c = I2C(0, scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))
        self.oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, self.i2c)
        self.clear()
        self.show_text("Smart Plant", "Booting...")

    def clear(self):
        self.oled.fill(0)
        self.oled.show()

    def show_text(self, line1="", line2="", line3=""):
        self.oled.fill(0)
        if line1:
            self.oled.text(line1, 0, 0)
        if line2:
            self.oled.text(line2, 0, 16)
        if line3:
            self.oled.text(line3, 0, 32)
        self.oled.show()
