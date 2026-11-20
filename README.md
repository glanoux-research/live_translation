# Live translation

A small client–server tool that translates spoken Korean into English text in real time, with an open-source speech model running on your own GPU. Nothing is sent to a cloud service.

## Why

I am a French student at Seoul National University, and most of my courses are taught in Korean. I tried three options before building this one:

- **Paid speech-to-text APIs.** They work well, but translating hours of lectures every week gets expensive.
- **Free online translators.** They are free, but the quality on spoken lectures is poor, and the lecturer's voice ends up on a third-party server.
- **Translation earbuds.** They rely on the same online translator, so they have the same problems.

This project keeps everything local: the audio stays on machines I control, and the model is free and open source.

## How it works

```
 microphone near the speaker
            │
            ▼
 laptop: client.py ── ffmpeg captures audio (16 kHz, mono, float32)
            │          and sends 0.2 s chunks over a WebSocket
            ▼
 desktop GPU: server.py ── faster-whisper large-v3 (float16)
            │               transcribes and translates Korean → English
            ▼
 laptop prints the English text as it arrives
```

- **Server (`server.py`):** collects audio until it has about 3 seconds, then runs Whisper's `translate` task with Korean as the source language. It sends the English text back only when it has changed. It keeps the last second of audio as context for the next window.
- **Client (`client.py`):** records a PulseAudio input with ffmpeg. It streams the audio to the server and prints each update as `LIVE: …`. A bounded buffer (5 s) keeps memory flat if the network stalls.

## Setup

My setup:
- a desktop with an 8 GB NVIDIA GPU running the server;
- a laptop running the client;
- a small USB microphone placed near the speaker;
- a VPN between the laptop and the desktop.

1. **Server (GPU machine):**

   ```bash
   pip install -r requirements.txt
   ./launch_server.sh          # listens on port 8765
   ```

   The first run downloads the `large-v3` model. On a smaller GPU, change the model name in `server.py`, for example to `medium` or `small`.

2. **Client (laptop, Linux with PulseAudio and ffmpeg):**

   ```bash
   pip install websockets numpy
   pactl list short sources     # find your microphone's name
   ```

   In `client.py`, set:
   - `DEVICE` to that source name;
   - `SERVER_URI` to `ws://<server address>:8765`.

   Then run:

   ```bash
   python client.py
   ```

## Limits

- **Source language:** Whisper's `translate` task only produces English. The source language is fixed to Korean in `server.py`.
- **Repeated text:** the server re-transcribes overlapping 3-second windows, so a sentence cut at a window edge can appear twice or lose a word.
- **No security on the connection:** the WebSocket is neither authenticated nor encrypted. Only run it on a private network or over a VPN.
- **Not measured:** latency and accuracy have not been measured against other tools yet.
- **Recording lectures:** ask the lecturer before recording a lecture, even for local, personal use.

## Credits

This project uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) and OpenAI's open [Whisper](https://github.com/openai/whisper) models, distributed through Hugging Face.

## Disclaimer

Claude, an AI assistant made by Anthropic, was used to build this repository.
