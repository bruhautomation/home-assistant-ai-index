# Contributing

Entries are one YAML file each in [`entries/`](entries/), validated against
[`schema/entry.schema.json`](schema/entry.schema.json). Harvested data lives in
`data/generated/` and is **bot-owned — never edit it in a PR**; the nightly
workflow regenerates it, and the renderer joins the two.

## Adding an entry

1. Copy an existing file in `entries/` (pick one with a similar shape — an
   add-on, a HACS integration, a core integration).
2. Fill in every field. The filename must equal the `id`.
3. Set the nine capability flags per the definitions below. **If you set a
   sensitive flag to true, cite it** (see Evidence).
4. Run the checks CI will run:

   ```bash
   pip install pyyaml jsonschema
   python tools/validate.py
   python tools/render_readme.py        # regenerates README tables
   ```

5. Open a PR. Harvested metrics for your entry appear after the next nightly run.

## The nine capability flags

A flag describes what the project **can** reach in its shipped form — including
things that require the user to opt in or configure a function, but excluding
things that would require modifying the project's code. When a capability is
opt-in, say so in `notes`. If you can't point to code that implements a
capability, the flag is false.

| Flag | True when the project… |
|---|---|
| `reads_entity_states` | reads the state or attributes of Home Assistant entities (whether bounded by Assist exposure or by an access token — say which in `notes`) |
| `reads_history` | queries recorder, history, logbook, statistics, or energy data |
| `reads_camera` | obtains camera images, streams, or recordings itself (being *sendable* a saved file by the user does not count — that's the sender's flag) |
| `listens_microphone` | processes live audio, including wake-word scoring and speech-to-text (where the audio then goes belongs in `data_sent`) |
| `controls_devices` | calls Home Assistant services that actuate devices, or exposes tools that do |
| `creates_automations` | writes automations, scripts, or helpers into the user's configuration |
| `edits_files` | writes configuration files or arbitrary filesystem paths (its own caches and media storage don't count) |
| `executes_code` | evaluates code chosen at runtime — shell, Python, SQL, or arbitrary Jinja templates — beyond declared service calls |
| `runs_unattended` | self-initiates AI activity by design: schedules, background loops, proactive triggers. Merely being callable from a user-written automation does **not** count — almost every service is. If the distinction matters for a project, explain it in `notes` (see the LLM Vision and AI Automation Suggester entries for the pattern) |

`inference`, `install`, `providers`, and `data_sent` are separate axes — a
capability flag never encodes *where* data goes, only *what can be reached*.

## Evidence

The index's premise is that claims about other people's code are citable. Five
flags — `reads_camera`, `listens_microphone`, `edits_files`, `executes_code`,
`runs_unattended` — **require** a citation when true, and CI enforces it:

```yaml
evidence:
  reads_camera:
    path: custom_components/llmvision/media_handlers.py
    line: 300
    commit: 3cc0510a4dfc8d8a05599eb9f7a0079979c80492
```

To get one: open the implementing line on GitHub, press `y` to pin the
permalink to a commit, and copy path/line/commit from the URL. Add an optional
`repo:` key when the evidence lives outside the entry's main repo (e.g. add-on
packaging). Citations welcome on any other flag too.

Evidence pins age as upstream code moves — that's by design (the claim was true
at that commit). Refreshing a stale pin is a great first PR.

## Corrections and disputes

If an entry misstates what a project can reach, open a
["This is wrong about my project"](https://github.com/bruhautomation/home-assistant-ai-index/issues/new?template=correction.yml)
issue. Maintainer reports get priority. While a claim is being resolved,
maintainers of this index add the flag to the entry's `disputed:` list so the
site marks it ⚠️ immediately — being honest about uncertainty beats being
quietly wrong.

## What gets listed

Anything that connects AI/LLM functionality to Home Assistant: integrations,
add-ons, MCP servers, model runtimes, voice components. Being in HACS is not
required; being installable and real is. Archived projects can stay listed —
the health data shows their state — but new entries for abandoned projects need
a reason.

Three anti-goals shape editorial calls: this is **not a scoreboard** (no
composite scores, no rankings), **not a HACS mirror** (entries exist because
someone checked what the code reaches), and **not a review site** (no opinions
on quality — facts with citations).

## For maintainers of listed projects

You're welcome to link back:

```markdown
[![Home Assistant AI Index](https://img.shields.io/badge/Home%20Assistant-AI%20Index-41BDF5?logo=home-assistant&logoColor=white)](https://github.com/bruhautomation/home-assistant-ai-index)
```

## Machine-readable data

The site publishes everything as
[`data.json`](https://bruhautomation.github.io/home-assistant-ai-index/data.json)
(CC BY 4.0): curated fields, harvested metrics, evidence pointers, and the
Supervisor rating breakdowns. Field names match the entry schema plus a
`generated` object per entry. Build on it.

## Tooling map

| Command | Does |
|---|---|
| `python tools/validate.py` | schema + evidence policy (CI gate) |
| `python tools/harvest.py` | refresh `data/generated/` (bot's job; `--no-api` works without a token) |
| `python tools/render_readme.py` | regenerate README tables (`--check` in CI) |
| `python tools/build_site.py` | build the static site into `_site/` |
| `python tools/test_rating.py` | rating-port regression tests |
