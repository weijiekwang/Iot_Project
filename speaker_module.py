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

        # 使用 I2S(1) 做 TX
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

    def play_chunk(self, chunk_bytes: bytes):
        """播放一小块 PCM 数据（16kHz,16bit,mono）。"""
        if not chunk_bytes:
            return
        self.i2s.write(chunk_bytes)

    def deinit(self):
        self.i2s.deinit()
        print("Speaker I2S deinit.")
