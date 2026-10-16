# App UI design (AT2B)

The Streamlit app's look and flow follow the Claude Design project **"UI Mockups Request"**
(https://claude.ai/design/p/325afcdb-33e6-407f-a496-7ac9c51a5f30), file `Skillabus Prototype v2.dc.html`
(Quan, 16 Oct 2026). That project is the source of truth for the design; this folder holds the
imported copy:

| File | What |
|---|---|
| `Skillabus Prototype v2.dc.html` | The v2 prototype: start, inputs, browse ads, results, evidence, subject drawer, chat. Template (`<x-dc>`) plus the mock logic (`<script data-dc-script>`). |
| `support.js` | The Claude Design runtime the template imports. It needs React from the Claude Design host, so the file does not render on its own: open it in the project above. |

Also in the project, not copied: `Skillabus Prototype.dc.html` (v1, more text per screen) and
`Skillabus Mockups.dc.html` (the board of three results directions and the other pages).

Design tokens used by `app/ui.py` and `.streamlit/config.toml`: dark charcoal (#121416 page, #0e1012 sidebar,
#1b1e22 cards), text #e8e6e1, muted #9a9a94; Literata for headlines, Public Sans for body, DM Mono for numbers
and subject codes; teal #4fd1b8 = have, amber #f2b74f = partial, rose #f06d84 = missing, violet #b89cff = emerging,
blue #8fbcff = links.

Re-import after edits in Claude Design: run /design-login once in an interactive Claude Code session, then read
the file with the DesignSync tool (get_file) and replace the copy here; the app does not read these files.
