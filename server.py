import asyncio
import websockets
import numpy as np
from faster_whisper import WhisperModel

model = WhisperModel("large-v3", compute_type="float16")
#medium-v2, small-v2, tiny-v2, base-v2, large-v3
  
SAMPLE_RATE = 16000
BUFFER_SECONDS = 3

async def handler(websocket):
    print("Client connected")

    audio_buffer = np.array([], dtype=np.float32)
    last_sent_text = ""

    async for message in websocket:
        chunk = np.frombuffer(message, dtype=np.float32)

        # accumulate audio
        audio_buffer = np.concatenate([audio_buffer, chunk])

        # process when enough audio collected
        if len(audio_buffer) >= SAMPLE_RATE * BUFFER_SECONDS:
            segments, _ = model.transcribe(audio_buffer, task="translate", language="ko", beam_size=5)
# language="ko"
# , initial_prompt="This is a korean course about Marine hydrodynamics. " \
#             "The course is designed for students who are interested in learning about the principles of fluid mechanics and their applications in the marine environment. " \
#             "The course covers topics such as fluid properties, fluid statics, fluid dynamics, and their applications in ship design, offshore structures")

            full_text = " ".join(seg.text for seg in segments).strip()

            # send only if changed
            if full_text != last_sent_text:
                await websocket.send(full_text)
                last_sent_text = full_text

            # keep last 1 second for context
            audio_buffer = audio_buffer[-SAMPLE_RATE:]
            
async def main():
    server = await websockets.serve(handler, "0.0.0.0", 8765)
    print("Server started on port 8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())