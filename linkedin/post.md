What if a bad software release could undo itself… in under a minute? 🤔

Here's how most teams release software:
👉 The new version replaces the old one, for everyone at once.
👉 If it has a hidden bug, every user hits it.
👉 Someone gets an alarm at 3 AM and has to decide, half asleep, whether to undo it.

So I built a project that releases software the way a good restaurant tests a new dish 🍽️

1️⃣ Serve it to one table first (about 20% of users)
2️⃣ Watch what happens: are requests failing? is it slow?
3️⃣ Happy guests → serve more tables, step by step, up to 100%
4️⃣ Unhappy guests → take it off the menu immediately. Everyone gets the old dish again.

The "watching" is done by numbers, not opinions. Every 30 seconds the system checks the new version only:
❌ Are more than 7.2% of requests failing?
⏱️ Are requests slower than 300 ms?
If yes twice, it rolls back automatically. No human needed.

🧪 I tested it on a Kubernetes cluster on my laptop:
✅ A healthy version was promoted to 100%
❌ A version with 25% failing requests was rolled back in 47 seconds
🐢 A version that was 600 ms slower was rolled back in 46 seconds
💥 When I switched off the monitoring, it refused to promote the release. No proof, no promotion.

📚 New to DevOps? I wrote a free study guide for this project. It explains every tool from zero (Docker, Kubernetes, Helm, Prometheus, Grafana, Argo Rollouts, GitHub Actions) and includes 8 hands-on labs and 25 interview questions. It's also available as a 42-page PDF.

👉 Swipe through the slides for the full picture: the problem, when to use it, architecture, how it works, results, and how to run it yourself in about 3 minutes.

💻 Code + study guide: https://github.com/sufyanahmadkamboh/sufyan-devops-slo-progressive-delivery
🌐 Slides + all my projects: https://sufyanahmadkamboh.github.io/#story=slo-progressive-delivery&slide=1

How does your team decide that a release is "good enough"? I'd love to hear in the comments 👇

#DevOps #Kubernetes #SRE #ProgressiveDelivery #ArgoRollouts #Prometheus #Grafana #CICD #LearningDevOps #CloudComputing
