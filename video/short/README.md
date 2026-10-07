# 1-minute short (vertical)

A 59-second vertical video (1080×1920, 30 fps) for YouTube Shorts, Instagram Reels and TikTok, built from code
like the long video. It opens on the result ("This release was broken. It rolled itself back in 42 seconds."), then
shows the problem, the canary + SLO check and the measured proof from the real run, and ends with a call to follow.

| File | What it is |
|---|---|
| `script.py` | the script: one entry per voiceover line, with the caption text, the visual and its sound effect |
| `build_short.py` | the pipeline: voiceover → timeline → animated page → frames → voice + sound effects (no music) → MP4 |
| `render.mjs` | renders every frame with headless Edge: the page exposes `render(t)`, each frame sets the time |
| `voiceover/` | the recorded voiceover (SpeakSay, voice "Steve"): one FLAC per line, `lines.json` (the exact spoken text and settings) and `words.json` (word timings for the captions) |
| `logos/` | Kubernetes, Prometheus and Argo icons from the CNCF artwork repository; the Grafana icon from the Grafana repository |
| `upload.md` | title, description and hashtags for the upload |

```bash
python video/short/build_short.py   # -> video/out/short/safe-releases-short-{full,silent}.mp4
```

How it holds attention:
- The first frame already shows the result; the voice starts at 0 s.
- The topic is clear on every frame: a header with the Kubernetes logo, "DevSecOps" and "Safe releases on Kubernetes",
  the DevOps loop (plan → monitor, + security) and the logo of each tool where it acts.
- A new visual on every line (every 1–6 s), and a sound effect on every cut.
- Big word-by-word captions (the current word is highlighted), so the video works without sound.
- Real numbers from the recorded run: 25% errors, 0.305 against a 0.072 limit, aborted after 42 s, +600 ms caught
  in 43 s. The screenshots are the real Grafana and Argo Rollouts captures in `video/shots/`.
- The voice runs 7% faster than recorded (pitch kept), and lines are 0.12 s apart.

Requirements: Python 3 with numpy and scipy, Node.js 22+, Microsoft Edge, Docker (ffmpeg pinned by digest).
The sound effects come from `../audio_assets.py` (synthesised; see `../AUDIO-LICENSES.md`).
