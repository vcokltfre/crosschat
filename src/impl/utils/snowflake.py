from time import time


class SnowflakeGenerator:
    def __init__(self, pid: int, wid: int) -> None:
        self.pid = pid
        self.wid = wid
        self.inc = 0

    def generate(self) -> int:
        ts = round(time() * 1000) - 1640995200000
        sf = ts << 22 | self.pid << 17 | self.wid << 12 | (self.inc % (1 << 12))

        self.inc += 1

        return sf
