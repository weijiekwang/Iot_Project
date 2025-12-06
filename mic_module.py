# mic_module.py
from machine import I2S, Pin
from config import (
    MIC_BCLK_PIN, MIC_LRCL_PIN, MIC_DOUT_PIN,
    MIC_SAMPLE_RATE, MIC_BITS, MIC_BUFFER_BYTES
)
import time

class MicRecorder:
    def __init__(self):
        self.bck = Pin(MIC_BCLK_PIN)
        self.ws  = Pin(MIC_LRCL_PIN)
        self.sd  = Pin(MIC_DOUT_PIN)
        self.buf = bytearray(MIC_BUFFER_BYTES)
        self.i2s = None
        self._init_i2s()

    def _init_i2s(self):
        """初始化或重新初始化I2S接口"""
        if self.i2s:
            try:
                self.i2s.deinit()
                time.sleep_ms(50)
            except:
                pass

        self.i2s = I2S(
            0,
            sck=self.bck,
            ws=self.ws,
            sd=self.sd,
            mode=I2S.RX,
            bits=MIC_BITS,
            format=I2S.MONO,
            rate=MIC_SAMPLE_RATE,
            ibuf=MIC_BUFFER_BYTES * 4
        )
        print("Mic I2S init OK")

    def reinit(self):
        """重新初始化I2S（用于解决I2S总线冲突）"""
        print("Reinitializing mic I2S...")
        self._init_i2s()

    def read_chunk(self):
        n = self.i2s.readinto(self.buf)
        if n:
            return bytes(self.buf[:n])
        return b""

    def deinit(self):
        if self.i2s:
            self.i2s.deinit()
