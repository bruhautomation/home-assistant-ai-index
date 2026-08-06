# Home Assistant AI Index

**What can this thing reach?** — the question every existing list skips.

Every roundup of Home Assistant AI integrations gives you stars and a name. None
answers the questions you actually have before installing one: can it see my
cameras? Can it act without me asking? Does my data leave my network, and where
does it go? This index answers those questions per project, with claims cited to
the project's own source code at a pinned commit.

**[Browse and filter the full index →](https://bruhautomation.github.io/home-assistant-ai-index/)**

## How to read this index

Each entry carries nine **capability flags** (what the project can reach), an
**inference** axis (where the model runs), and an **install surface**:

| | Capability | Meaning |
|---|---|---|
| 📖 | reads states | Reads the states of entities exposed to it |
| 📜 | reads history | Queries recorder / history / logbook data |
| 📷 | reads camera | Accesses camera images or streams |
| 🎙️ | microphone | Processes live audio |
| 🎛️ | controls devices | Calls Home Assistant services to actuate devices |
| ⚙️ | creates automations | Writes automations, scripts, or helpers |
| 📝 | edits files | Writes to configuration files or the filesystem |
| ⚡ | executes code | Runs arbitrary code beyond declared service calls |
| ⏰ | unattended | Self-initiates AI activity on schedules or triggers by design |

**Inference:** 🏠 local · ☁️ cloud · 🏠/☁️ your choice of backend decides.
The combinations are the point: *cloud inference + camera access* means your
camera frames leave your network. *Unattended + controls devices* means it can
act on your home without you asking. Filter for exactly that on
[the site](https://bruhautomation.github.io/home-assistant-ai-index/).

Capability flags on sensitive claims (camera, microphone, file writes, code
execution, unattended operation) link to the exact line of source that
implements them, pinned to a commit. Add-on entries additionally show the
permissions their packaging requests and Home Assistant's own
[add-on security rating](https://developers.home-assistant.io/docs/add-ons/security/),
computed by the Supervisor's published algorithm — that is the only score you
will find here.

## What this is not

- **Not a scoreboard.** No composite security score, no ranking. Tables sort
  alphabetically; facts carry evidence links instead of grades.
- **Not a HACS mirror.** Being installable is not the bar — being understood is.
  Entries exist because someone checked what the project can reach.
- **Not a review site.** No opinions on whether a project is good. Capability
  facts, data-flow facts, health metrics, and Home Assistant's own rating math.

## This is wrong about my project

If this index misstates what your project can reach, that is the bug we care
about most.
**[Open a correction →](https://github.com/bruhautomation/home-assistant-ai-index/issues/new?template=correction.yml)**
Maintainer corrections get priority handling, and a disputed flag is marked ⚠️
on the site immediately while it is resolved.

<!-- BEGIN GENERATED -->
_The index tables are generated from `entries/` + `data/generated/` by
`tools/render_readme.py`. First harvest pending._
<!-- END GENERATED -->

## Contributing

Add a project by copying an entry in [`entries/`](entries/) and opening a PR —
[CONTRIBUTING.md](CONTRIBUTING.md) defines every capability flag objectively so
flags are checkable, not vibes. Or use the
[submit-a-project issue form](https://github.com/bruhautomation/home-assistant-ai-index/issues/new?template=submit-project.yml)
and we'll do the research.

Maintainers of listed projects are welcome to link back:

```markdown
[![Home Assistant AI Index](https://img.shields.io/badge/Home%20Assistant-AI%20Index-41BDF5?logo=home-assistant&logoColor=white)](https://github.com/bruhautomation/home-assistant-ai-index)
```

## Data

Everything on the site is published as machine-readable JSON at
[`data.json`](https://bruhautomation.github.io/home-assistant-ai-index/data.json)
— a stable, documented artifact you can build bots and dashboards on. Harvested
metrics refresh nightly; each entry page shows exactly when.

## License

Tool code is [MIT](LICENSE). Catalog content (entries, tables, published data)
is additionally [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) —
reuse with attribution to "Home Assistant AI Index".
