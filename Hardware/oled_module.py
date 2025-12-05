# oled_module.py
from machine import I2C, Pin
from config import OLED_WIDTH, OLED_HEIGHT, OLED_SCL_PIN, OLED_SDA_PIN

try:
    import ssd1306
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False
    print("Warning: ssd1306 not found, OLED disabled")

class OledDisplay:
    def __init__(self):
        if not OLED_AVAILABLE:
            self.oled = None
            return
        
        try:
            self.i2c = I2C(0, scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN), freq=400000)
            self.oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, self.i2c)
            self.clear()
            self.show_text("Smart Plant", "Booting...")
            print("OLED initialized")
        except Exception as e:
            print("OLED init failed:", e)
            self.oled = None

    def clear(self):
        if self.oled:
            self.oled.fill(0)
            self.oled.show()

    def show_text(self, line1="", line2="", line3=""):
        if not self.oled:
            return
        
        try:
            self.oled.fill(0)
            if line1:
                self.oled.text(line1[:16], 0, 0)  # 最多16个字符
            if line2:
                self.oled.text(line2[:16], 0, 16)
            if line3:
                self.oled.text(line3[:16], 0, 32)
            self.oled.show()
        except Exception as e:
            print("OLED display error:", e)
