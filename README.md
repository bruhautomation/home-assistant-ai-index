# Home Assistant AI Index

**What can this thing reach?** — the question every existing list skips.

Every roundup of Home Assistant AI integrations gives you stars and a name. None
answers the questions you actually have before installing one: can it see my
cameras? Can it act without me asking? Does my data leave my network, and where
does it go? This index answers those questions per project, with claims cited to
the project's own source code at a pinned commit.

**[Browse and filter the full index →](https://bruhautomation.github.io/home-assistant-ai-index/)**

[![The index site: preset questions, capability filters, comparison](docs/site-preview.png)](https://bruhautomation.github.io/home-assistant-ai-index/)

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
**25 projects indexed**, metrics harvested 2026-08-06. Sorted by name — never by stars. [Filter, compare, and see the evidence on the site →](https://bruhautomation.github.io/home-assistant-ai-index/)

### Conversation agents

| Name | Capabilities | Inference | Install | Health | |
|---|---|---|---|---|---|
| [Anthropic Claude](https://github.com/home-assistant/core) | 📖🎛️ | ☁️ cloud | core | part of core | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/anthropic-conversation/) |
| [Azure OpenAI Conversation](https://github.com/joselcaguilar/azure-openai-ha) | 📖🎛️ | ☁️ cloud | HACS | — | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/azure-openai-conversation/) |
| [Extended OpenAI Conversation](https://github.com/jekalmin/extended_openai_conversation) | 📖📜🎛️⚙️📝⚡ | 🏠/☁️ choice | HACS | — | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/extended-openai-conversation/) |
| [Google Generative AI](https://github.com/home-assistant/core) | 📖🎛️ | ☁️ cloud | core | part of core | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/google-generative-ai/) |
| [Home LLM](https://github.com/acon96/home-llm) | 📖🎛️ | 🏠/☁️ choice | HACS | — | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/home-llm/) |
| [Ollama](https://github.com/home-assistant/core) | 📖🎛️ | 🏠 local | core | part of core | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/ollama-conversation/) |
| [OpenAI Conversation](https://github.com/home-assistant/core) | 📖🎛️ | ☁️ cloud | core | part of core | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/openai-conversation/) |

### Agent platforms

| Name | Capabilities | Inference | Install | Health | |
|---|---|---|---|---|---|
| [Home Generative Agent](https://github.com/goruck/home-generative-agent) | 📖📜📷🎛️⚙️⏰ | 🏠/☁️ choice | HACS | — | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/home-generative-agent/) |

### Vision

| Name | Capabilities | Inference | Install | Health | |
|---|---|---|---|---|---|
| [Frigate](https://github.com/blakeblackshear/frigate) | 📷🎙️⏰ | 🏠/☁️ choice | add-on, container | 🛡️ 6/8 | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/frigate/) |
| [LLM Vision](https://github.com/valentinfrlch/ha-llmvision) | 📷 | 🏠/☁️ choice | HACS | — | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/llm-vision/) |

### Automation authoring

| Name | Capabilities | Inference | Install | Health | |
|---|---|---|---|---|---|
| [AI Automation Suggester](https://github.com/ITSpecialist111/ai_automation_suggester) | 📖 | 🏠/☁️ choice | HACS | — | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/ai-automation-suggester/) |

### Model Context Protocol

| Name | Capabilities | Inference | Install | Health | |
|---|---|---|---|---|---|
| [hass-mcp](https://github.com/voska/hass-mcp) | 📖📜🎛️ | 🏠/☁️ choice | container, external | — | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/hass-mcp/) |
| [MCP Server (core)](https://github.com/home-assistant/core) | 📖🎛️ | 🏠/☁️ choice | core | part of core | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/mcp-server/) |
| [Model Context Protocol (client)](https://github.com/home-assistant/core) | — | 🏠/☁️ choice | core | part of core | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/mcp-client/) |

### Agent tools & frameworks

| Name | Capabilities | Inference | Install | Health | |
|---|---|---|---|---|---|
| [AI Task (core framework)](https://github.com/home-assistant/core) | 📷⏰ | 🏠/☁️ choice | core | part of core | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/ai-task/) |

### Model runtimes

| Name | Capabilities | Inference | Install | Health | |
|---|---|---|---|---|---|
| [LocalAI](https://github.com/mudler/LocalAI) | — | 🏠 local | container, external | — | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/localai/) |

### Voice stack

| Name | Capabilities | Inference | Install | Health | |
|---|---|---|---|---|---|
| [Assist Microphone](https://github.com/home-assistant/addons) | 🎙️ | 🏠 local | add-on | official add-on · 🛡️ 5/8 | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/assist-microphone/) |
| [microWakeWord](https://github.com/kahrendt/microWakeWord) | 🎙️ | 🏠 local | external | — | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/microwakeword/) |
| [OpenAI TTS](https://github.com/sfortis/openai_tts) | — | ☁️ cloud | HACS | — | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/openai-tts/) |
| [openWakeWord](https://github.com/rhasspy/wyoming-openwakeword) | 🎙️ | 🏠 local | add-on, container | 🛡️ 5/8 | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/openwakeword-addon/) |
| [Piper (text-to-speech)](https://github.com/rhasspy/wyoming-piper) | — | 🏠 local | add-on, container | 🛡️ 5/8 | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/piper-addon/) |
| [Speech-to-Phrase](https://github.com/OHF-Voice/speech-to-phrase) | 📖🎙️ | 🏠 local | add-on, container | 🛡️ 5/8 | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/speech-to-phrase/) |
| [Whisper (speech-to-text)](https://github.com/rhasspy/wyoming-faster-whisper) | 🎙️ | 🏠 local | add-on, container | 🛡️ 5/8 | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/whisper-addon/) |
| [Wyoming Satellite](https://github.com/rhasspy/wyoming-satellite) | 🎙️ | 🏠 local | external | — | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/wyoming-satellite/) |

### Dashboards & UI

| Name | Capabilities | Inference | Install | Health | |
|---|---|---|---|---|---|
| [View Assist](https://github.com/dinki/View-Assist) | 📖 | 🏠/☁️ choice | external | — | [→](https://bruhautomation.github.io/home-assistant-ai-index/entries/view-assist/) |
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
