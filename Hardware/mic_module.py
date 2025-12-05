# mic_module.py
from machine import I2S, Pin
from config import (
    MIC_BCLK_PIN, MIC_LRCL_PIN, MIC_DOUT_PIN,
    MIC_SAMPLE_RATE, MIC_BITS, MIC_BUFFER_BYTES
)

class MicRecorder:
    def __init__(self):
        self.bck = Pin(MIC_BCLK_PIN)
        self.ws  = Pin(MIC_LRCL_PIN)
        self.sd  = Pin(MIC_DOUT_PIN)

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
        self.buf = bytearray(MIC_BUFFER_BYTES)
        print("Mic I2S init OK")

    def read_chunk(self):
        n = self.i2s.readinto(self.buf)
        if n:
            return bytes(self.buf[:n])
        return b""

    def deinit(self):
        self.i2s.deinit()
