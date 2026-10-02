# LinkedIn package

| File | Use |
|---|---|
| `post.md` | Post text, written for a beginner audience |
| `carousel/carousel.pdf` | **Recommended:** upload as a *Document* post. LinkedIn shows it as a swipeable carousel |
| `carousel/slide-01.png` … `slide-11.png` | The same slides as images (1080×1350), for a multi-image post |
| `carousel/slides.html` | Source of the slides. Edit it and re-render each slide with a headless browser (`slides.html?s=N`) |
| `project-image.png` | Single architecture image (1200×627) |
| `project-summary.md` | Short technical summary |
| `hashtags.txt` | Hashtags |

## The slides (visual first: one picture per idea, short captions)

| # | Visual | Message |
|---|---|---|
| 1 | Side-by-side: bug hits 5/5 users vs 1/5 behind a shield | What the project does |
| 2 | 4-panel comic strip (deploy → bug → 3 AM alarm → manual undo) | The pain point |
| 3 | Traffic-split diagram: users → 1 NEW + 4 old servers, magnifier on NEW | The idea |
| 4 | Icon grid + "skip it when" panel | When to use it |
| 5 | 5-step icon flow | How a team uses it |
| 6 | Connected architecture diagram inside the Kubernetes boundary | Architecture |
| 7 | Two gauges (errors, p95) → green/red decision + fail-safe | Implementation |
| 8 | Bar chart: seconds from release to decision | Measured results (lab) |
| 9 | Metro-map learning path through the tools + stats | Study material |
| 10 | Staircase of terminal windows | How to run it yourself |
| 11 | QR codes to the repo and portfolio | Links + question |

## How to post

1. Start a post, choose **Add a document**, and upload `carousel/carousel.pdf`.
2. Give it a title, for example *"Releases that undo themselves: explained simply"*.
3. Paste the text from `post.md`.
