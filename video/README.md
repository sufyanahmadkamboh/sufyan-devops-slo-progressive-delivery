# Video: Safe releases that undo themselves

An explainer of this project for beginners, as a conversation between a senior DevOps engineer and a junior
colleague. The first half explains the idea in plain words: the problem, SLIs, SLOs, error budgets and burn rates,
the architecture and the code. The second half is a **real run of the lab** on a local kind cluster:
- a healthy release promoted;
- an error regression and a latency regression rolled back automatically;
- a Prometheus outage that fails safe;
- the NetworkPolicy test, and the tests and CI.

Two versions are built:

| File (in `video/out/part01/`, not committed) | What it is |
|---|---|
| `safe-releases-that-undo-themselves-full.mp4` | picture, narration and sound effects (no music) |
| `safe-releases-that-undo-themselves-silent.mp4` | the identical picture stream, with no audio track |

Every audio asset, with its license and timestamps, is listed in [AUDIO-LICENSES.md](AUDIO-LICENSES.md).

## How it is made

| File | What it does |
|---|---|
| `record.sh` | runs the whole lab once and records it: every command with its real output, exit code and duration (`recordings/NN-name.txt`), a rollout snapshot every 4 seconds while releases run (`recordings/watch/`), and screenshots of the Grafana and Argo Rollouts dashboards; it deletes the cluster at the end |
| `capture.mjs` | takes the dashboard screenshots during the run (headless Edge, DevTools protocol) |
| `pick_shots.py` | chooses the screenshots shown in the video by the moments in the rollout snapshots (`shots/README.md`) |
| `series.py`, `scenes.py`, `demo.py` | the script: the scenes, the narration and the visuals; every number is read from the recordings |
| `components.py` | building blocks: cards, diagrams, terminals, code excerpts |
| `build.py` | the pipeline: page → frames → narration → encode → captions and chapters → post-production |
| `production.py`, `audio_assets.py` | the title and end cards, and the sound effects (synthesised in code) |
| `voiceover/part01/` | the recorded voiceover: one FLAC per narrated step, generated with SpeakSay (senior: "Steve", junior: "Cora"), and `lines.json`, the exact text each file says |
| `tts.ps1` | fallback narration with the Windows speech engine, used only when a video has no recorded voiceover |
| `redact.py` | checks that nothing identifying (account IDs, private e-mail addresses) reaches a frame or a caption |
| `youtube/part01/` | upload package: title, description with chapters, captions (SRT), thumbnail |

## Build

Requirements: Python 3 with `pygments`, `Pillow`, `numpy` and `scipy`, Node.js 22+,
Microsoft Edge, and Docker (ffmpeg runs in a container pinned by digest). Recording also needs the lab's tools
(`kind`, `kubectl`, `helm`) and the `kubectl-argo-rollouts` plugin.

```bash
bash video/record.sh             # about 20 minutes: the real run (only needed to refresh the recordings)
python video/pick_shots.py       # choose the dashboard screenshots
python video/build.py 1          # frames, narration, encode, post-production
python video/build.py licenses   # AUDIO-LICENSES.md
```

The run uses `ci/fast-values.yaml` (analysis every 15 s, 30 s pauses), like the end-to-end test; the thresholds are
the same as in production.
