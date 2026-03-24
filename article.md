# From Baymax to CareMax: I Built the Health Buddy That Doesn't Exist Yet

---

*"On a scale of 1 to 10, how would you rate your pain?"*

If you've seen *Big Hero 6*, you know Baymax — that big puffy robot who scans you head-to-toe, pulls up your entire medical history, and tells you exactly what's going on. No waiting rooms. No digging through drawers for that one lab report from last March.

I walked out of the theater thinking: why don't we have anything even close to that?

What we actually have is a pile of crumpled reports somewhere in a desk, a foggy memory that "something was a bit off last time," and a doctor who gets about seven minutes to figure you out. Your health data — probably the most personal thing you own — is scattered across hospital printouts, email attachments, and a random photo you snapped of a lab sheet and immediately forgot about.

So I started building. Not the inflatable robot (not yet anyway), but something that could actually work today.

I called it **CareMax**.

---

## The Problem With "Normal"

This happens to literally everyone:

Annual check-up. Doctor glances at your numbers. "Creatinine is 98. Normal." Cool, you move on.

Next year — 105. Still in range. "Normal."

Year after that — 112. Still technically "normal."

But nobody's connecting the dots. 88 → 98 → 105 → 112 over four years. Each time looks fine on its own. The trend, though? That's a different story. By the time someone finally flags it as "abnormal," you've missed years of catching it early.

The data was always there. It's just that nobody could see it as a story instead of isolated snapshots.

That's the first thing CareMax does. Snap a photo of your lab report. The AI reads it, pulls out every number, figures out that "HGB" and "血红蛋白" and "Hb" are all the same thing, and draws your trends. Across years, across hospitals, across your whole family.

Suddenly that creatinine line has a slope, and it's hard to look away.

---

## Getting AI to Actually Read Medical Reports

Sounds easy, right? Just OCR the paper. Done.

Nope.

A blood test from Beijing looks nothing like one from Shenzhen. One hospital writes "WBC," another writes "白细胞," a third uses "White Blood Cells" in a completely different column layout. Some reports are nice clean PDFs. Others are blurry photos taken at 45 degrees with someone's thumb in the corner.

We ended up building a whole pipeline. First, PaddleOCR rips through the image and spits out raw text. Then a big language model — Qwen3 — takes that text plus the original image and actually *understands* it. It knows that "135 g/L" next to "HGB" means your hemoglobin is 135. It knows an upward arrow means something's off. It even knows how to split a single long screenshot into two separate reports if that's what you uploaded.

And here's the fun part: if you throw 5 photos at it — 3 from one check-up, 2 from another — it figures out on its own which pages belong together. It's not just reading. It's thinking.

The whole thing runs on free models. PaddleOCR and DeepSeek-OCR for the text extraction, Qwen3-VL-32B for the smart part. Total API cost per scan: zero.

---

## "Hey, How's My Liver Doing?"

This is where it clicks.

We're in the age of AI agents now. Claude, Cursor, Copilot — they write code, manage tasks, browse the web. But ask them about your cholesterol trend? Nothing. Ask them to scan a check-up report? Blank stare.

So CareMax works as an **agent skill**. You install it once:

```bash
npx skills add KittenYang/caremax-skills
```

And now your AI assistant can talk to your health data. You're sitting in your terminal and you say:

> *"Show my creatinine trend for the past year."*

The agent checks if you're logged in. If not, it pops open a browser — you click "Allow" once — done. It pulls your data and shows you the chart. No app to open. No website. No password to remember.

Or you drag in a photo of a check-up report:

> *"Scan this for me."*

It creates a session, uploads the image, runs OCR with real-time progress updates, shows you what it found — "2 reports detected, 24 indicators total, 3 abnormal" — and waits for you to say "looks good, save it." Nothing gets saved without your OK.

Or the killer feature:

> *"Have I ever had abnormal liver function results?"*

That's not a database query. That's a natural language search across your entire medical history. It knows "liver function" means ALT, AST, GGT, bilirubin. It digs through every report you've ever uploaded and comes back with the two times your ALT was high, complete with dates, values, and what the normal range should be.

That's Baymax. Not the suit — the brain.

---

## One Account, Whole Family

Health isn't a solo thing. My mom sends me photos of her lab results asking "is this OK?" My dad's got diabetes and someone needs to watch his HbA1c. My wife wants to check if the baby's bilirubin is going down.

CareMax handles all of that. One account, multiple family members. Upload a report for your mom, the system keeps her indicators separate from yours. Say "show my mom's blood sugar trend" and it knows who you mean.

---

## Sessions, Not Files

Here's a design choice I'm proud of.

Old way: you upload a file, system creates a record, done. Except — what if you upload 3 photos of the same report? What if one long screenshot has 2 different reports in it? What if you started uploading but closed the browser halfway through?

New way: everything is a **session**. You upload 3 photos, they all go into one session. The AI analyzes all of them together, figures out there are actually 2 reports, shows you the results, you confirm, and both reports save atomically. If you close the browser before confirming, the session is still there — just pick up where you left off next time.

Delete a session? Everything goes away — the files, the reports, the indicators. Clean. Atomic. No orphaned data floating around.

---

## Why a Skill Instead of an App

We actually did build a web app. Charts, dashboards, the whole thing. But then I realized something:

**Nobody opens a health tracking app on purpose.**

You don't wake up and think "let me check my health dashboard." But you do ask questions: "What was my cholesterol?" "Is this report normal?" "How's dad's kidney function doing?"

By making CareMax an agent skill, it lives wherever your AI assistant lives — your terminal, your editor, your chat. The data is always one question away. Not one app-download-sign-up-find-the-right-page away.

Works with Claude Code, Cursor, Copilot, and 40+ other agents. Same skill, same data, everywhere.

---

## What Baymax Got Right

Baymax wasn't cool because of the armor or the rocket fist. He was cool because he was just... there. He already knew your history. He didn't need you to open an app or explain what happened last time. He just cared.

We're not fully there yet. You still need to upload your reports (for now). But the direction is right:

**Your health data should be alive — something you can talk to, ask questions about, track over time, share with family — from any AI interface.**

Not in a drawer. Not locked in some hospital system. Not rotting in your camera roll.

Alive. And always one question away.

---

*CareMax is open source. Try it:*

```bash
npx skills add KittenYang/caremax-skills
```

*Then tell your agent: "Show my health indicators."*

*Baymax would approve.*
