"""Keeps the last crash report in non-volatile memory, so it survives a reset.

The board prints it to the serial console on startup. To read it from the REPL:

    import microcontroller
    from tt_scoreboard.crash_log import CrashLog
    print(CrashLog(microcontroller.nvm).load())

CrashLog(microcontroller.nvm).clear() forgets it.
"""

# Blob layout at the start of the region: magic, text length (2 bytes), text.
_MAGIC = b"TE"
_HEADER_SIZE = 4
# Bytes at the end of the memory kept for the crash log; the stats use the rest.
SIZE = 1024
# Marks a report cut short to fit: the start is dropped, since the error itself
# is at the end of a traceback.
_TRUNCATED = b"...\n"


class CrashLog:

    def __init__(self, memory, size=SIZE):
        if size <= _HEADER_SIZE + len(_TRUNCATED) or size > len(memory):
            raise ValueError("Crash log size does not fit the memory")
        self._memory = memory
        self._start = len(memory) - size
        self._size = size

    def load(self):
        """Return the saved report, or None if there is none or it is damaged."""
        start = self._start
        header = bytes(self._memory[start:start + _HEADER_SIZE])
        if header[0:2] != _MAGIC:
            return None
        length = int.from_bytes(header[2:4], "big")
        if _HEADER_SIZE + length > self._size:
            return None
        data = bytes(self._memory[start + _HEADER_SIZE:start + _HEADER_SIZE + length])
        try:
            return data.decode()
        except UnicodeError:
            return None

    def save(self, report):
        """Save report in place of the previous one.

        Nothing is written if the same report is already saved, so a crash
        that repeats on every restart doesn't keep rewriting the memory.
        """
        data = report.encode()
        room = self._size - _HEADER_SIZE
        if len(data) > room:
            data = _TRUNCATED + data[len(data) - room + len(_TRUNCATED):]
            # Don't start in the middle of a multi-byte character.
            while data[len(_TRUNCATED)] & 0xC0 == 0x80:
                data = _TRUNCATED + data[len(_TRUNCATED) + 1:]
        blob = _MAGIC + len(data).to_bytes(2, "big") + data
        start = self._start
        if bytes(self._memory[start:start + len(blob)]) == blob:
            return
        self._memory[start:start + len(blob)] = blob

    def clear(self):
        start = self._start
        self._memory[start:start + _HEADER_SIZE] = bytes(_HEADER_SIZE)
