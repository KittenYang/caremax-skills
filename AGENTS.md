# Guidance for AI Agents Working in This Repo

This repository contains **CareMax Health** skills for AI coding agents. When editing or adding skills, follow these rules.

## Repo structure

- **skills/** — Each subdirectory is one skill. The CLI and agents discover skills by scanning `skills/` for directories that contain `SKILL.md`.
- **Skill directory name** must exactly match the `name` in that skill's frontmatter (e.g. `skills/caremax-auth/` <> `name: caremax-auth`).

## SKILL.md requirements

- **Frontmatter (YAML):**
  - `name` (required): lowercase, hyphens only, max 64 chars, must match parent directory name.
  - `description` (required): what the skill does and when to use it; include trigger terms so agents know when to apply it. Max 1024 chars.
  - `license` (optional): e.g. `MIT` if the skill is under the repo license.
- **Body:** Markdown instructions. Keep under ~500 lines; put long reference material in `references/` or `scripts/` and link from SKILL.md.

## Conventions

- Write descriptions in **third person** (e.g. "Use when..." not "You can use when...").
- Be concise; avoid restating general API docs. Focus on correct usage, authentication flow, and error handling.
- When adding a new skill: create `skills/<skill-name>/SKILL.md`, then update README.md "Skills" table and `skills/llms.txt`.
- **Agent-facing** indicator/record helpers often use `/api/skill/*` with OAuth (`api-call.sh`). **User app** features may use other authenticated JSON routes (e.g. quick vitals under `/api/indicators/*`).
- **Do not document privileged operator or admin-only APIs in this public repository.** Keep deployer runbooks in private docs or the application repo if appropriate.
- Authentication for end users uses OAuth Device Flow — do not hardcode user tokens in skills.

## References

- [Agent Skills specification](https://agentskills.io/specification.md)
- [skills CLI (discovery, install)](https://github.com/vercel-labs/skills)
- [CareMax API OpenAPI Spec](https://api.caremax.ai/openapi.yaml)
