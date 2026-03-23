# From Baymax to CareMax: Building the Health Companion That Doesn't Exist Yet

---

*"On a scale of 1 to 10, how would you rate your pain?"*

If you've watched *Big Hero 6*, you remember Baymax — the inflatable healthcare companion who scans you head-to-toe, cross-references your medical history, and calmly tells you exactly what's going on with your body. No appointments. No waiting rooms. No flipping through stacks of paper reports trying to remember which number was high last time.

I watched that movie and thought: **we have none of this.**

What we have instead is a drawer full of crumpled check-up reports, a vague memory that "something was a little high last time," and a doctor who has seven minutes to figure out what you've been doing for the past year. Your health data — the most personal data you own — lives scattered across hospital printouts, PDF attachments, and that one photo you took of a lab sheet and forgot about in your camera roll.

I decided to fix this. Not with an inflatable robot (yet), but with something that could actually exist today.

I called it **CareMax**.

---

## The Drawer Problem

Here's a scenario that happens to everyone:

You go for an annual check-up. The doctor glances at your report and says, "Your creatinine is 98. That's normal." You nod and move on.

A year later, another check-up. Creatinine is 105. Still within range. "Normal," the doctor says.

Another year. 112. Still "normal." Still within the reference range printed on that piece of paper.

But here's the thing — **no one is looking at the trend.** Your creatinine went from 88 → 98 → 105 → 112 over four years. Each snapshot looks fine. The trajectory tells a completely different story. By the time it crosses the reference range and someone says "abnormal," you've lost years of early intervention.

The problem isn't that the data doesn't exist. It's that no one — not you, not your doctor — has an easy way to **see it over time.**

That's the first thing CareMax does. You take a photo of your lab report. AI reads it, extracts every indicator, standardizes the names (because different hospitals call the same test different things), and plots your trends. Instantly. Across years. Across hospitals. Across family members.

That creatinine trend? Now it's a line on a chart, and the slope is hard to ignore.

---

## Teaching AI to Read Your Reports

OCR on medical reports sounds simple until you try it.

A blood test report from Beijing looks nothing like one from Shanghai. Hospital A prints hemoglobin as "HGB," Hospital B writes "血红蛋白," and Hospital C uses "Hb" with the unit in a completely different column. Some reports are clean PDFs. Others are photos taken at an angle with a coffee stain on the corner.

We threw everything at a large language model. Not just OCR — **structured extraction.** The AI doesn't just read text; it understands what a medical report *is*. It knows that "135 g/L" next to "HGB" means hemoglobin is 135 grams per liter. It knows that an arrow pointing up means abnormal. It knows that "检查日期 2024.12.21" is a date that should be formatted as 2024-12-21.

Then comes the hard part: **standardization.** When you upload reports from three different hospitals over five years, you end up with "白细胞," "WBC," "White Blood Cells," and "白血球" — all referring to the same thing. CareMax uses an LLM to maintain a personal indicator dictionary for each user, automatically mapping every variant to a canonical name. It even learns new synonyms over time.

The result: you upload a photo, and thirty seconds later you have structured, searchable, trendable health data.

---

## "Hey Agent, How's My Liver?"

Here's where it gets interesting.

We live in the age of AI agents. Claude Code, Cursor, Copilot — they're already writing code, managing tasks, browsing the web. But they can't tell you if your cholesterol is trending up. They can't scan a medical report. They can't cross-reference your family's health history.

So we built CareMax as an **agent skill.**

Think about what this means. You're sitting in your terminal — or any AI interface — and you say:

> *"Show my creatinine trend for the past year."*

The agent silently checks if it has access to your CareMax account. If not, it opens a browser, you click "Allow" once (OAuth Device Flow — the same thing GitHub CLI uses), and that's it. Forever authenticated. Then it pulls your data and shows you the trend. Right there. No app to open. No website to navigate. No password to remember.

Or you take a photo of a check-up report and say:

> *"Upload and scan this."*

The agent uploads it, runs OCR, extracts 23 indicators, flags the 2 abnormal ones, and saves everything — all in one breath.

Or the one that gets me every time:

> *"Have I ever had abnormal liver function results?"*

This isn't a database query. This is **semantic search** across your entire medical history. The AI understands that "abnormal liver function" means it should look for elevated ALT, AST, GGT, bilirubin — even if you never mentioned those specific tests. It finds the two reports from 2024 where your ALT was high and shows them to you, with dates, values, and reference ranges.

**This is Baymax.** Not the inflatable suit, but the part that actually matters — an AI that knows your health history and can answer questions about it in natural language.

---

## Your Family's Health, One Account

Health isn't individual. My mom texts me photos of her lab reports and asks "is this okay?" My dad has diabetes and needs someone to track his HbA1c trend. My wife wants to know if the baby's bilirubin is going down.

CareMax supports family member profiles under one account. Upload a report for your mom, tag it as hers, and her indicator dictionary stays separate from yours. Ask the agent "show my mom's blood sugar trend" and it knows exactly who you mean.

---

## Why a Skill, Not an App

We could have built a beautiful mobile app with charts and dashboards. In fact, we did — CareMax started as a web app. But here's what I realized:

**People don't want another app. They want answers.**

Nobody wakes up and thinks "I should open my health tracking app today." But people do ask questions: "What was my cholesterol last time?" "Is this report normal?" "How's my dad's kidney function trending?"

By building CareMax as an agent skill, we meet users where they already are — in their AI assistant, their code editor, their terminal. The health data is always one question away, not one app-download-and-login away.

The installation is literally one command:

```bash
npx skills add KittenYang/caremax-skills
```

After that, any compatible AI agent — Claude Code, Cursor, Copilot, and 40+ others — can access your health data (with your permission, of course).

---

## What Baymax Got Right

Baymax wasn't impressive because of his armor or his rocket fist. He was impressive because he was **always there, always watching, always understanding.** He didn't need you to explain your medical history. He already knew. He didn't need you to open an app. He just... cared.

We're not there yet. CareMax still needs you to upload your reports. It can't scan you through the screen (maybe in a few years). But the core idea is the same:

**Your health data should be alive — searchable, trendable, queryable in natural language, accessible from any AI interface, for your whole family.**

Not sitting in a drawer. Not locked in a hospital's system. Not forgotten in your camera roll.

Alive. And always one question away.

---

*CareMax is open source. The agent skills are at [github.com/KittenYang/caremax-skills](https://github.com/KittenYang/caremax-skills). Try it:*

```bash
npx skills add KittenYang/caremax-skills
```

*Then ask your agent: "Show my health indicators."*

*Baymax would be proud.*
