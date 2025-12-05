# speaker_module.py
from machine import I2S, Pin
from config import (
    AMP_BCLK_PIN, AMP_LRCL_PIN, AMP_DIN_PIN,
    AMP_SAMPLE_RATE, AMP_BITS
)

class SpeakerPlayer:
    def __init__(self):
        self.bck = Pin(AMP_BCLK_PIN)
        self.ws  = Pin(AMP_LRCL_PIN)
        self.sd  = Pin(AMP_DIN_PIN)

        self.i2s = I2S(
            1,
            sck=self.bck,
            ws=self.ws,
            sd=self.sd,
            mode=I2S.TX,
            bits=AMP_BITS,
            format=I2S.MONO,
            rate=AMP_SAMPLE_RATE,
            ibuf=4000
        )
        print("Speaker I2S init OK")

    def play_pcm(self, pcm_bytes):
        """播放一段 16-bit mono PCM 数据"""
        if not pcm_bytes:
            return
        view = memoryview(pcm_bytes)
        # 分块写入，避免一次写太大
        chunk = 1024
        for i in range(0, len(view), chunk):
            self.i2s.write(view[i:i+chunk])

    def deinit(self):
        self.i2s.deinit()
