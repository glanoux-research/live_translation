import asyncio
import websockets
import numpy as np
from collections import deque
import subprocess

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.2
DEVICE = "alsa_output.usb-GeneralPlus_USB_Audio_Device-00.analog-stereo.monitor"
SERVER_URI = "ws://0.0.0.0:8765"

MAX_BUFFER = SAMPLE_RATE * 5  # prevent memory explosion


async def send_audio(websocket, buffer):
    samples_per_chunk = int(SAMPLE_RATE * CHUNK_DURATION)

    while True:
        if len(buffer) >= samples_per_chunk:
            chunk = [buffer.popleft() for _ in range(samples_per_chunk)]
            audio_chunk = np.array(chunk, dtype=np.float32)

            await websocket.send(audio_chunk.tobytes())
        else:
            await asyncio.sleep(0.01)  # small wait


async def receive_text(websocket):
    async for message in websocket:
        print("LIVE:", message)


def start_ffmpeg_stream(buffer):
    command = [
        "ffmpeg",
        "-re",  # IMPORTANT
        "-f", "pulse",
        "-i", DEVICE,
        "-fflags", "nobuffer",
        "-flags", "low_delay",
        "-f", "f32le",
        "-acodec", "pcm_f32le",
        "-ac", "1",
        "-ar", str(SAMPLE_RATE),
        "-"
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=0
    )

    while True:
        if process.poll() is not None:
            print("FFmpeg stopped!")
            break

        data = process.stdout.read(4096)
        if not data:
            continue

        audio = np.frombuffer(data, dtype=np.float32)
        buffer.extend(audio)

        # prevent infinite growth
        while len(buffer) > MAX_BUFFER:
            buffer.popleft()


async def main():
    async with websockets.connect(SERVER_URI) as websocket:
        buffer = deque()

        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, start_ffmpeg_stream, buffer)

        await asyncio.gather(
            send_audio(websocket, buffer),
            receive_text(websocket)
        )


if __name__ == "__main__":
    asyncio.run(main())