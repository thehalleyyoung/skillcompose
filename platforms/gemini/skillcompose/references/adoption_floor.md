# Adoption floor (no popularity ceiling)

Highly popular skills are **first-class**. There is **no default ceiling** on installs or stars. `/skillremix` upgrades and remixes any marketplace skill that clears a minimum adoption signal — including mega skills with hundreds of thousands of installs.

Do **not** describe picks as “middling examples.” Prefer: *eligible* / *adoption-floor* / *marketplace skill*.

## Default install floor (skills.sh)

- **Include:** installs **≥ 80** (no upper bound; mega OK)
- **Reject low:** `< 80` — too thin to teach adoption lessons
- **Optional cap only:** `--max-installs N` if a *specific run* should exclude mega skills (off by default)

## GitHub stars (when installs unknown)

- **Include:** stars **≥ 15** (no upper bound)
- If both signals exist, **installs win** for eligibility
- **Optional cap only:** `--max-stars N` (off by default)

## Portable skill shape

Must have `SKILL.md` (Agent Skills layout). Prefer packages installable via `npx skills add owner/repo@skill`.

## Name traps

| Query | Wrong-sense hits |
|---|---|
| story / novel | Storybook, user-story agile skills |
| book | book-illustrator, PDF book converters |
| agent | generic “agent playbook” with no SKILL.md |
| verify | unrelated CI “verify” actions |
| prototype | security “prototype pollution” |

## Sampling tip

Run 3–5 `npx skills find` queries across domains; collect eligible hits (popular included); pick with `pick_eligible.py` (seeded) or `--pin`. Legacy script names `pick_middling.py` / `pick_n_middling.py` still work as aliases.
