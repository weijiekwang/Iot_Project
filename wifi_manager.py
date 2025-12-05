# wifi_manager.py
import network
import time
from config import WIFI_SSID, WIFI_PASSWORD

def connect_wifi(max_retries=20):
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to WiFi:", WIFI_SSID)
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        retries = 0
        while not wlan.isconnected() and retries < max_retries:
            retries += 1
            print("  waiting...", retries)
            time.sleep(1)

    if wlan.isconnected():
        print("WiFi connected:", wlan.ifconfig())
        return True
    else:
        print("WiFi connect failed")
        return False
