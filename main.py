# main.py
# Process:
# 1. WiFi connection
# 2. Continuous listening mode: constantly record and send to server
# 3. Say "hello world" to start conversation, say "bye bye" to end conversation
# 4. Receive server's voice response and play through speaker

import time
import usocket as socket
import ujson
import ntptime
import machine

from wifi_manager import connect_wifi
from mic_module import MicRecorder
from speaker_module import SpeakerPlayer
from moisture_sensor_module import MoistureSensor
from oled_module import OledDisplay
from config import (
    MIC_SAMPLE_RATE,
    MIC_BITS,
    MIC_BUFFER_BYTES,
    SERVER_IP,
    SERVER_PORT,
    AUDIO_API_PATH,
    DEVICE_ID,
    MOISTURE_SENSOR_PIN,
    MOISTURE_READ_INTERVAL,
    NTP_HOST,
    NYC_UTC_OFFSET,
)

RECORD_SECONDS = 5   # Record for 5 seconds each time, giving users enough time to speak complete sentences


def sync_time_from_ntp():
    """
    Sync time from NTP server and set RTC to New York time.
    Returns True if successful, False otherwise.
    """
    try:
        print("[NTP] Syncing time from NTP server...")
        ntptime.settime()  # This sets UTC time
        print("[NTP] UTC time synced successfully")

        # Get current UTC time
        utc_time = time.time()

        # Apply NYC timezone offset (UTC-5 for EST, UTC-4 for EDT)
        nyc_time = utc_time + (NYC_UTC_OFFSET * 3600)

        # Set RTC to NYC time
        tm = time.localtime(nyc_time)
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))

        print("[NTP] Time set to New York timezone (UTC{:+d})".format(NYC_UTC_OFFSET))
        print("[NTP] Current NYC time: {:02d}:{:02d}:{:02d}".format(tm[3], tm[4], tm[5]))
        return True

    except Exception as e:
        print("[NTP] Failed to sync time:", e)
        return False


def get_current_time_str():
    """
    Get current time as formatted string (HH:MM).
    Uses local time from the RTC (already set to NYC time).
    """
    current = time.localtime()
    hour = current[3]
    minute = current[4]
    return "{:02d}:{:02d}".format(hour, minute)


def send_moisture_data(moisture_data):
    """
    Send moisture sensor data to server via HTTP POST.

    Args:
        moisture_data: Dictionary with moisture sensor readings
    """
    try:
        # Build TCP connection
        addr_info = socket.getaddrinfo(SERVER_IP, SERVER_PORT)[0][-1]
        s = socket.socket()
        s.settimeout(5.0)
        s.connect(addr_info)

        # Prepare JSON data
        json_data = ujson.dumps(moisture_data)

        # Build HTTP POST request
        path = "/api/moisture"
        headers = (
            "POST {} HTTP/1.1\r\n"
            "Host: {}:{}\r\n"
            "Content-Type: application/json\r\n"
            "Content-Length: {}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).format(path, SERVER_IP, SERVER_PORT, len(json_data))

        # Send request
        s.write(headers.encode("utf-8"))
        s.write(json_data.encode("utf-8"))

        # Read response (optional, just to complete the request)
        response = s.recv(256)

        s.close()
        print("[Moisture] Data sent to server")

    except Exception as e:
        print("[Moisture] Failed to send data to server:", e)


def record_and_stream(mic, seconds):
    """
    Record audio and stream to /api/stt via HTTP POST,
    return complete conversation response data.
    """
    bytes_per_sample = MIC_BITS // 8  # 16bit -> 2 bytes
    total_bytes = MIC_SAMPLE_RATE * bytes_per_sample * seconds

    print("Recording {} seconds...".format(seconds))

    # Clear I2S buffer to ensure microphone is in good state
    try:
        dummy_buf = bytearray(512)
        for _ in range(5):
            mic.i2s.readinto(dummy_buf)
            time.sleep_ms(10)
    except:
        pass

    # 1. Build TCP connection
    addr_info = socket.getaddrinfo(SERVER_IP, SERVER_PORT)[0][-1]
    s = socket.socket()
    s.connect(addr_info)

    path = AUDIO_API_PATH + "?device_id=" + DEVICE_ID

    headers = (
        "POST {} HTTP/1.1\r\n"
        "Host: {}:{}\r\n"
        "Content-Type: application/octet-stream\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).format(path, SERVER_IP, SERVER_PORT, total_bytes)

    s.write(headers.encode("utf-8"))

    # 2. Record and send simultaneously
    bytes_sent = 0
    mv = memoryview(mic.buf)

    while bytes_sent < total_bytes:
        remaining = total_bytes - bytes_sent
        this_chunk = MIC_BUFFER_BYTES if remaining >= MIC_BUFFER_BYTES else remaining

        n = mic.i2s.readinto(mv[:this_chunk])
        if not n:
            time.sleep_ms(2)
            continue

        s.write(mv[:n])
        bytes_sent += n

    print("Audio sent, waiting for response...")

    # 3. Read HTTP response
    response = b""
    while True:
        data = s.recv(512)
        if not data:
            break
        response += data

    s.close()

    # 4. Parse JSON
    try:
        header, body = response.split(b"\r\n\r\n", 1)
    except ValueError:
        print("Failed to split HTTP response")
        return None

    try:
        obj = ujson.loads(body)
    except Exception as e:
        print("JSON parse error:", e)
        return None

    # Return complete response object
    return obj


def stream_tts_from_server():
    """
    Stream TTS audio from server and play, avoiding large memory allocation.
    Receive and play simultaneously, not storing entire audio on ESP32.
    """
    speaker = SpeakerPlayer()

    try:
        # Build TCP connection
        addr_info = socket.getaddrinfo(SERVER_IP, SERVER_PORT)[0][-1]
        s = socket.socket()
        s.connect(addr_info)

        # Send HTTP GET request
        path = "/api/tts"
        req = (
            "GET {} HTTP/1.1\r\n"
            "Host: {}:{}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).format(path, SERVER_IP, SERVER_PORT)

        s.write(req.encode("utf-8"))
        print("Requesting TTS audio...")

        # Read HTTP response headers
        buf = b""
        while b"\r\n\r\n" not in buf:
            data = s.recv(256)
            if not data:
                break
            buf += data
            if len(buf) > 1024:
                break

        # Separate headers and body
        if b"\r\n\r\n" in buf:
            header, body = buf.split(b"\r\n\r\n", 1)
        else:
            header = buf
            body = b""

        # Body already has first chunk of audio data
        if body:
            speaker.play_chunk(body)

        # Stream receive and play remaining audio
        total_bytes = len(body)
        while True:
            data = s.recv(512)
            if not data:
                break
            speaker.play_chunk(data)
            total_bytes += len(data)

        s.close()
        print("Played {} bytes".format(total_bytes))

    except Exception as e:
        print("TTS playback error:", e)

    finally:
        speaker.deinit()
        # Force garbage collection to free memory immediately after playback
        import gc
        gc.collect()
        # Wait for speaker to fully release I2S bus
        time.sleep_ms(100)


def check_and_play_gesture_tts():
    """
    Check if server has gesture recognition TTS audio, play if available.
    """
    try:
        # Build TCP connection
        addr_info = socket.getaddrinfo(SERVER_IP, SERVER_PORT)[0][-1]
        s = socket.socket()
        s.settimeout(3.0)
        s.connect(addr_info)

        # Send HTTP GET request
        path = "/api/gesture_tts"
        req = (
            "GET {} HTTP/1.1\r\n"
            "Host: {}:{}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).format(path, SERVER_IP, SERVER_PORT)

        s.write(req.encode("utf-8"))

        # Read HTTP response headers
        buf = b""
        while b"\r\n\r\n" not in buf:
            data = s.recv(256)
            if not data:
                break
            buf += data
            if len(buf) > 1024:
                break

        # Separate headers and body
        if b"\r\n\r\n" in buf:
            header, body = buf.split(b"\r\n\r\n", 1)
        else:
            s.close()
            return False

        # Check if there's audio data
        if not body:
            # Read remaining data
            data = s.recv(512)
            if not data:
                s.close()
                return False
            body = data

        # If there's audio data, play it
        if body:
            print("[Gesture TTS] Received audio, playing...")
            speaker = SpeakerPlayer()
            try:
                # Play first chunk
                speaker.play_chunk(body)

                # Stream receive and play remaining audio
                total_bytes = len(body)
                while True:
                    data = s.recv(512)
                    if not data:
                        break
                    speaker.play_chunk(data)
                    total_bytes += len(data)

                print("[Gesture TTS] Played {} bytes".format(total_bytes))
            finally:
                speaker.deinit()
                # Force garbage collection after gesture TTS playback
                import gc
                gc.collect()
                time.sleep_ms(100)

            s.close()
            return True

        s.close()
        return False

    except Exception as e:
        print("[Gesture TTS] Error:", e)
        return False


def main():
    # 1. WiFi connection
    if not connect_wifi():
        print("WiFi connect failed, exit.")
        return

    # 2. Sync time from NTP server
    print("\n" + "=" * 50)
    print("Syncing time with NTP server...")
    print("=" * 50)
    if sync_time_from_ntp():
        print("[OK] Time synchronized to New York timezone")
    else:
        print("[WARNING] Time sync failed, using default time")
    time.sleep(1)

    print("\n" + "=" * 50)
    print("Smart Plant - Continuous Listening Mode")
    print("Say 'Hello World' to start conversation")
    print("Say 'Bye Bye' to end conversation")
    print("Gesture Recognition: Hi, Wow, Good")
    print("=" * 50)

    # 3. Initialize microphone, moisture sensor and OLED display
    mic = MicRecorder()
    moisture_sensor = MoistureSensor(MOISTURE_SENSOR_PIN)
    oled = OledDisplay()
    conversation_active = False
    last_moisture_read = time.time()
    last_gesture_check = time.time()

    # Initialize display
    oled.show_text("Smart Plant", "Initializing...")

    try:
        # Continuous listening loop
        while True:
            # Periodically read moisture sensor and update OLED display
            current_time = time.time()
            if current_time - last_moisture_read >= MOISTURE_READ_INTERVAL:
                moisture_data = moisture_sensor.read_all()
                print("\n[Moisture Sensor]")
                print("  Raw: {:4d} | Voltage: {:.2f}V | Moisture: {:.1f}% | Status: {}".format(
                    moisture_data["raw"],
                    moisture_data["voltage"],
                    moisture_data["moisture_percent"],
                    moisture_data["status"]
                ))

                # Update OLED display with current time and moisture
                time_str = get_current_time_str()
                moisture_str = "Moist: {:.1f}%".format(moisture_data["moisture_percent"])
                oled.show_large_text(time_str, moisture_str)
                print("[OLED] Updated display: {} | {}".format(time_str, moisture_str))

                # Send moisture data to server
                send_moisture_data(moisture_data)

                last_moisture_read = current_time

            # Periodically check for gesture recognition TTS audio (check every 1 second)
            if current_time - last_gesture_check >= 1.0:
                if check_and_play_gesture_tts():
                    # After playing gesture TTS, reinitialize microphone
                    mic.reinit()
                    time.sleep_ms(50)
                last_gesture_check = current_time

            print("\n[Listening...]")

            # Record and send to server
            result = record_and_stream(mic, RECORD_SECONDS)

            if result:
                user_text = result.get("text", "")
                response_text = result.get("response", "")
                action = result.get("action", "")
                has_audio = result.get("has_audio", False)
                conversation_active = result.get("conversation_active", False)

                print("\n" + "=" * 50)
                print("RESULT FROM SERVER:")
                print("  User text: '{}'".format(user_text))
                print("  Response: '{}'".format(response_text))
                print("  Action: '{}'".format(action))
                print("  Has audio: {}".format(has_audio))
                print("  Conversation active: {}".format(conversation_active))
                print("=" * 50)

                # Display recognized text
                if user_text:
                    print("\n[YOU]: {}".format(user_text))

                # Display bot's response
                if response_text:
                    print("[BOT]: {}".format(response_text))

                    # Stream play voice response (avoid large memory allocation)
                    if has_audio:
                        print("[Playing voice response...]")
                        stream_tts_from_server()

                        # Reinitialize microphone I2S (resolve I2S conflict after speaker use)
                        mic.reinit()
                        time.sleep_ms(50)
                else:
                    print("[BOT]: (no response)")

                # Handle conversation state changes
                if action == "start_conversation":
                    print("\n*** Conversation Started! ***\n")
                elif action == "end_conversation":
                    print("\n*** Conversation Ended ***\n")

            # Brief delay
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\nStopping...")

    except Exception as e:
        print("Error:", e)

    finally:
        mic.deinit()
        print("System shutdown complete.")


if __name__ == "__main__":
    main()
