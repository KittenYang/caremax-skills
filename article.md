# No Baymax? CareMax.

---

*"On a scale of 1 to 10, how would you rate your pain?"*

If you've seen *Big Hero 6*, you know the deal. Baymax shows up, scans you, already knows your history, and explains what's going on in that absurdly reassuring voice. No waiting room. No archaeology in a desk drawer for last year's lab slip.

I'll be honest: walking out of the theater, I felt a little cheated. The screen gets a full-stack healthcare sidekick. Real life gets a pile of paper and a calendar reminder we keep snoozing.

What we actually live with: crumpled printouts, a fuzzy memory that "something was a bit off last time," and a clinician who has roughly seven minutes to reverse-engineer your last twelve months. Your health data — about as personal as data gets — is scattered across hospital PDFs, email attachments, and a photo in your camera roll you took, swiped away, and never opened again.

So I built something. Not the inflatable robot — I don't have the budget or the legal team for that yet — but something that works **today**.

It's called **CareMax**.

---

## The Trap Hidden Inside the Word "Normal"

Everyone has lived this story; fewer people admit they got played.

Annual check-up. A glance at the sheet: creatinine 98. Normal. You nod and leave.

Next year: 105. Still in range. Normal.

The year after: 112. Still "normal."

But the **arc**? 88 → 98 → 105 → 112 across four years. Each snapshot looks fine. Strung together, it's a different movie. By the time someone finally says "abnormal," you've often already paid the time tax.

The data was always there. Nobody was reading it as a **narrative**. CareMax starts there: snap a photo of a report, pull every value, reconcile that HGB, 血红蛋白, and Hb are the same underlying thing, and draw trends across years, hospitals, and family members. Once that creatinine line has a slope, it's surprisingly hard to unsee.

---

## Teaching Machines to Read Lab Reports: Easy on a Slide Deck, Humbling in Production

Sounds trivial, right? "Just OCR it."

Sure. And while we're at it, let's unify every hospital's layout, typography, and bilingual abbreviations with positive thinking.

A Beijing panel looks nothing like a Shenzhen one. One hospital prints "WBC," another writes 白细胞, a third uses English in a column you've never seen before. Some files are civilized PDFs. Others are 45° lifestyle photography with a thumb auditioning for the corner.

There's no secret sauce in the backend — just a pipeline built by **losing polite arguments with real hospital layouts**: pull text out of scans and PDFs, then read **layout**, not only numbers — how many separate reports are hiding in one long screenshot, and if you upload five photos, which ones belong to the same visit.

There's also **checkpointed resume**. OCR half-finishes, the network blinks, a worker sneezes — you retry and pick up where you left off, not from zero. That's an engineering detail until you've watched users retry uploads at 11 p.m.; then it's a small act of mercy.

Finally we **normalize indicators** — every eccentric label and unit gets folded into an internal dictionary so trends and search stay coherent.

---

## The Weather Changed: OpenClaw, CLIs, and the Skill Gold Rush

If you've been anywhere near builder circles lately, you've probably heard the name **OpenClaw** — a self-hosted agent stack with a serious CLI, a first-class `skills` workflow, and public registries like **ClawHub** where capabilities install like plugins ([OpenClaw docs](https://docs.openclaw.ai/) spell out the commands and load paths). Agents aren't new; what's new is how **they've moved into the terminal and the IDE** — the places you already live — instead of dying the moment you close a chat tab.

The memes caught fire in parallel: an **AI chief of staff** wiring tools into pipelines, the **one-person company** with an automation crew, and **hiring AI to run repeatable work** so you stop being the human cron job. It still sounds like late-night infomercial copy until you've shipped with it — then it's just embarrassingly practical.

Vendors noticed. The pattern is blunt: ship **official CLI + skills** so **Cursor, Claude Code, Copilot, OpenClaw-class runtimes**, and the long tail of agent hosts can **invoke your product without tab-hopping and copy-paste archaeology**. A skill is starting to look like a **consulate inside your dev environment** — install once, and the agent knows the auth dance and your API surface.

CareMax as a skill is half necessity — health data demands OAuth, context, and careful persistence — and half timing: **if trustworthy services are supposed to sit beside the agent you already trust**, another siloed mobile icon is a hard sell.

---

## "So… How's My Liver?" — A Question Most Assistants Can't Actually Answer

Agents write code, wrangle tasks, browse for you — all very impressive.

Ask them for your cholesterol trend or drop in a check-up photo, though, and you often get a polite shrug: **not because they're lazy, but because they're not wired to your data**.

CareMax ships as an **agent skill**. Install once:

```bash
npx skills add KittenYang/caremax-skills
```

Under the hood it's **OAuth device flow**: when auth is needed, a browser window opens, you approve once, scripts poll until the token lands — no hand-rolled curl choreography, no user-hostile multi-step scavenger hunt.

Then, from your terminal, editor, or chat:

> *"Show my creatinine trend for the past year."*

Want to **quick-log** today's weight or blood pressure? Same preset keys as the app's one-tap chips — the agent hits the API and you're done, no full report required.

Uploads are **session-based**: upload → streamed OCR (progress lines as they arrive) → you review → you confirm before anything hits the database. **No confirmation, no persistence** — not virtue signaling, just the minimum respect privacy deserves.

Ask something gnarlier:

> *"Have I ever had sketchy liver numbers?"*

That's not a cute `SELECT`. The backend runs a **stacked search**: LLM keyword extraction from natural language, LIKE passes across titles and summaries, vector retrieval, then **RAG** — a plain-language answer with **citations** so you know which report each sentence grew from, not which paragraph the model hallucinated.

That's the Baymax part I'm chasing: maybe not the vinyl shell, but **a brain that earned the right to speak**.

---

## One Account, Whole Family, Zero Drama

Health isn't a solo sport. My mom texts lab photos asking "is this OK?" My dad's on diabetes watch. Someone always cares about bilirubin trending down.

CareMax supports **family members** with clean separation. Say "show my mom's glucose trend" and it knows who you mean — **slightly more reliable than the family group chat where everyone read your message and collectively decided to think about it later**.

---

## Sessions, Not One-Shot File Uploads

Most products treat upload as **one file, one row**. That falls apart fast — three screenshots of the same report, two reports in one panoramic image, tab closed mid-upload.

CareMax runs the whole upload as one **session** — multiple images, one pass: detect report groups, structure, review, then **atomic confirm**. Close the tab early? The session waits; you resume. Delete a session? Files, derived reports, indicators go together — **no mystery cruft floating in the database**.

---

## Why a Skill Instead of Another App You'll Never Open

We built the web app too — charts, dashboards, the respectable adult version.

Then a boring truth landed: **almost nobody wakes up craving a "health tracking" icon**. People ask questions: what was my last LDL? is this sheet alarming? how's dad's kidney function trending?

Embedding CareMax in an agent puts the data **where you already work** — terminal, IDE, chat. One sentence away, not download → sign up → find the right screen → reset password → remember why you opened the app. It also lines up with the wave above: **your business rides along with the agent**, instead of begging users to chase another destination app.

Claude Code, Cursor, Copilot, OpenClaw, and 40+ other agent environments can use the same skill against the same account. Same data, same questions, **wherever your attention already is**.

---

## What Baymax Actually Got Right

Baymax wasn't cool because of the armor or the rocket fist. He was cool because he was **already there** — history loaded, tone calibrated, no lecture about which app to open first.

We're not at full score yet. You still upload your own reports (for now). Nobody gets a hug from the API. But the vector I'm betting on is simple:

**Health data should be alive — something you can talk to, interrogate, trend, and share with family — reachable from the AI surface you already use.**

Not in a drawer. Not locked in a hospital silo. Not composting next to food photos in your camera roll.

Alive. And one honest question away.

---

*CareMax is open source. Start here:*

```bash
npx skills add KittenYang/caremax-skills
```

*Then tell your agent: "Show my health indicators."*

*Baymax nods on screen. In the real world, we'll settle for getting this part right first.*
