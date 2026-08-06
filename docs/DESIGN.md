# DEDSEC Site — Design System

Landing page for the DEDSEC reconnaissance framework, published to
`https://aether-dz.github.io/dedsec/` from `docs/` on `main`.

**Style source:** opencode.ai aesthetic (warm near-black, monospace-only,
flat depth, ASCII terminal hero) — same system as the HuntPack landing.

## 1. Goal

A method-first landing that reads like a terminal session: what DEDSEC is,
how the 6-stage recon pipeline works, the 26 modules, and how to install it —
with zero marketing fluff. Evidence-driven tone matches the tool itself
("PoC or nothing" → "observation, not conclusion").

## 2. Color tokens

| Role | Token | Value | Use |
|------|-------|-------|-----|
| Canvas | `--bg` | `#201d1d` | Page background, button fills (warm near-black) |
| Surface/elevated | `--bg-elevated` | `#302c2c` | Terminal windows, code blocks, hover fills |
| Border/warm | `--border` | `rgba(15,0,0,.12)` | Hairline separators |
| Border/outline | `--border-strong` | `#646262` | Container outlines, button borders |
| Text/primary | `--text-1` | `#fdfcfc` | Headlines, body, button text |
| Text/secondary | `--text-2` | `#9a9898` | Lead, captions, muted links |
| Text/muted | `--text-3` | `#84848a` | Metadata (lifted from #6e6e73 for WCAG AA) |
| Accent | `--accent` | `#00e063` | Brand emerald — links, focus, key highlights |
| Success | `--ok` | `#30d158` | SUCCESS outcomes |
| Danger | `--err` | `#ff3b30` | CONFIRMED findings |
| Warning | `--warn` | `#ff9f0a` | PARTIAL / candidates |

## 3. Typography tokens

- `--mono`: `"Berkeley Mono", "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", Courier New, monospace`
- h1: `38px` / weight 700 / line-height 1.5
- h2: `16px` / weight 700 / line-height 1.5
- body: `16px` / weight 400 / line-height 1.5
- caption: `14px` / line-height 2.0 (nav links, labels)
- terminal mono: `14px` / line-height 1.6 (ASCII blocks)

## 4. Spacing tokens

Base 8px: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96.
Radius: `4px` only (`--r-default`), `6px` inputs. Content width
`min(880px, 100% - 48px)`.

## 5. Rules

- Flat depth: hairlines (`1px var(--border)`) only. No shadows, no gradients, no pills.
- Motion: `120ms ease-out` color/border transitions only. **No reveal-on-scroll.**
- Links: underline `1px`, `3px` offset, hover → accent + 2px underline. Nav links: no underline, hover accent.
- Buttons: `4px 20px` padding, `1px solid var(--border-strong)`, radius 4px, hover border `#8a8888` + accent text.
- ASCII terminal: `pre.term` in `--bg-elevated`, colored spans per token (`--accent` prompts, `--ok` confirmations, `--warn` candidates, `--text-3` frame).
- Rows (skills/modules): hairline-separated `li` grid, hover `--bg-elevated`, name → accent on hover. **No cards.**
- Nav: sticky `64px`, solid `--bg`, bottom hairline. Mobile: burger toggle, `aria-expanded`.
- A11y: skip-link, `:focus-visible` accent outline, `prefers-reduced-motion` kills transitions, all text ≥ AA on `--bg`.

## 6. Page structure

1. Header: `dedsec_` brand + nav (`pipeline`, `modules`, `usage`, `install`) + GitHub button
2. Hero: h1 "Recon that keeps receipts." + ASCII terminal demo scan
3. Pipeline: 6 stages as rows (Understand → Recon → Hunt → Discipline → Validate → Report)
4. Modules: grouped rows (`// discovery`, `// posture`, `// endpoint`) — 26 modules, key + one-liner
5. Usage: code-block install + example command with copy buttons
6. Footer: brand, doc links, MIT note

## 7. Performance & build

- Single `styles.css` (~9KB), single `app.js` (~1.8KB, copy buttons + nav toggle only)
- No external fonts/requests; `theme-color` `#201d1d`
- Served from `/docs` with `.nojekyll` (byte-identical deployment)
- meta description + canonical + OG/Twitter tags

## 8. Accepted debt

- No Lighthouse run in this environment (no browser) — structural checks only.
- Terminal ASCII art is hand-fixed width; verified for balance but not pixel-tested.
