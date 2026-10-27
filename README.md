# Subtitle Tools

Cross-platform tools to create SubRip (`.srt`) subtitles from speech and translate existing SRT files. Transcription and translation are separate workflows: you can use either one without setting up the other's AI service. Windows and Linux installer scripts configure the defaults. At launch, each tool lets you choose GUI dialogs or CLI-only interaction.

## Choose a workflow

| Command | Input | Result | AI/runtime |
| --- | --- | --- | --- |
| `uv run subtitle-transcribe` | Local audio/video or a YouTube URL | Timed SRT in the detected speech language | Faster-Whisper; Node.js is additionally needed for YouTube extraction |
| `uv run universaltranslator` | Existing SRT | SRT translated to a selected target language | TranslateGemma served locally by Ollama |

The translator asks for both the source and target language. GUI mode uses dropdowns; CLI mode uses numbered menus. Its menu includes 36 common languages. Language codes are included in the prompt because that is the prompt format recommended for TranslateGemma.

## Quick setup: Windows

Install [uv](https://docs.astral.sh/uv/) if needed:

```powershell
winget install --id astral-sh.uv
```

Open PowerShell in this project folder and run:

```powershell
.\setup.ps1
```

The installer runs `uv sync`, then asks for GUI/CLI default mode, Whisper model and device, Ollama model, and Ollama API URL. It asks whether to save these choices in `.env` for future runs; the default is No. If you decline, choices apply only to this setup session and a tool launched from it, while any existing `.env` remains unchanged. The installer then offers to launch either tool. Choose Enter to finish setup without launching a tool. `.env` is ignored by Git and is not included in the repository.

## Quick setup: Linux

CLI-only use requires Python 3.11, 3.12, or 3.13. GUI mode additionally needs Tkinter and an active graphical session. On Debian or Ubuntu, install the system Python and optional Tkinter package. For example:

```bash
sudo apt update
sudo apt install python3 python3-tk
```

Check that `python3 --version` is between 3.11 and 3.13. If you plan to use GUI mode, also check `python3 -c 'import tkinter'`. If your distribution's default Python is outside the supported range, install a supported Python version and, for GUI mode, its matching Tk package.

Install uv using the [official instructions](https://docs.astral.sh/uv/getting-started/installation/), then run from the project directory:

```bash
bash setup.sh
```

The Linux installer verifies uv and a supported Python interpreter, runs `uv sync`, and prompts for the same configuration as Windows. Tkinter is checked only when GUI is selected as the default. It offers to save choices in `.env` (default No), then offers the same two tools. If you only want to set up dependencies, use `uv sync --python "$(command -v python3)"` directly.

Install Node.js through your Linux distribution's package manager if you plan to use YouTube URLs. Install Ollama separately if you plan to translate subtitles.

For YouTube extraction on Linux, install Node.js with your distribution's package manager, then verify it with `node --version`. Without Node.js, yt-dlp may warn that some YouTube formats are unavailable; some videos can still download, but extraction is less reliable.

### Linux with Ollama on another host

If Ollama runs on another computer or host, `localhost` in Linux will refer to the Linux machine, not that Ollama host. Set the endpoint to an address Linux can reach:

```bash
export SUBTITLE_OLLAMA_URL="http://OLLAMA_HOST:11434/api/generate"
curl "http://OLLAMA_HOST:11434/api/tags"
uv run universaltranslator
```

Replace `OLLAMA_HOST` with the Ollama machine's hostname or IP address. The tags request should include `translategemma`. Configure Ollama to listen on an interface reachable from Linux and allow the connection through the host's firewall. Translation requests and subtitle text are sent to the configured Ollama host. If Ollama runs on the same Linux machine, the default `http://localhost:11434/api/generate` URL is appropriate.

You can also use the tools directly on Windows PowerShell or Linux Bash:

```sh
uv run subtitle-transcribe
uv run universaltranslator
```

`uv run` uses the project's `.venv` and synchronizes it when needed. Each command asks which interface to use; pressing Enter accepts the installer-saved default. `uv.lock` records resolved versions for repeatable installs. Keep this lockfile committed; do not commit `.venv` or `.env`.

If PowerShell blocks the setup script, allow it for the current PowerShell process only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```

## Requirements by workflow

### Transcription

- **Faster-Whisper** is the speech recognition engine. It runs locally and downloads its model files on first use.
- **PyAV** reads audio streams from supported media containers, including MP4. The project constrains PyAV to versions compatible with Faster-Whisper's decoder API.
- **Node.js** is required only when extracting YouTube audio. `yt-dlp` uses Node plus its `ejs:github` remote component to solve YouTube's JavaScript challenges. The component can be fetched from GitHub at runtime.
- **Internet access** is needed to install dependencies, download the Whisper model on first use, and retrieve YouTube audio.
- **Tkinter** supplies GUI dialogs and language dropdowns. It is required only for GUI mode; CLI-only mode does not import Tkinter. It is included with standard Windows Python installers and is a separate package on many Linux distributions.

The tool uses the `large-v3` Whisper model on CPU with int8 compute by default. This favors transcription quality over speed and memory usage; first-time model download and transcription may take a while.

### Translation

- **Ollama** runs the translation model on your computer. Start its local service before translating.
- **TranslateGemma** is the default translation model. Download it once with `ollama pull translategemma`.
- Translation sends one subtitle block at a time to Ollama's local HTTP endpoint. The original SRT indices and timestamps are retained.

Translation does not require Node.js or Faster-Whisper. Transcription does not require Ollama or TranslateGemma.

## Why TranslateGemma?

TranslateGemma is a Gemma-family model tuned specifically for translation, rather than a general chat model being asked to translate as a secondary task. The [Ollama model page](https://ollama.com/library/translategemma) describes it as supporting 55 languages and lists 4B, 12B, and 27B variants.

The default `translategemma` tag is the 4B variant, listed by Ollama at about 3.3 GB. That is a relatively modest model download for a dedicated multilingual translator and is a reasonable starting point on consumer hardware. It runs locally, so there is no per-request API bill and subtitle text stays on the machine when using the default local Ollama URL.

“No API bill” does not mean zero cost: the model uses disk, RAM/VRAM, electricity, and your computer's processing time. Runtime memory needs can be higher than the model download size. Translation quality varies by language pair and context; review important subtitles rather than assuming a model output is perfect.

Larger variants trade resource use for a chance at better results, not a guarantee:

| Ollama model | Approximate download size on the Ollama page | When to consider it |
| --- | ---: | --- |
| `translategemma` / `translategemma:4b` | 3.3 GB | Default; lower resource use and a good first try |
| `translategemma:12b` | 8.1 GB | Try if the 4B output is not good enough and your computer has more memory |
| `translategemma:27b` | 17 GB | Higher resource requirement; for capable hardware and cases where quality merits slower processing |

Download a larger variant explicitly before selecting it in configuration. Other translation models can also be used if they support Ollama's `/api/generate` endpoint and follow the same prompt format, but results and language coverage will differ.

## Configuration

The installers can optionally save these settings in `.env`; choose No to keep them limited to the setup session. You can edit `.env` to change saved defaults. Environment variables in the current shell override `.env` values.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SUBTITLE_INTERFACE` | `gui` | Saved default interface: `gui` or `cli`; the app asks on each launch |
| `SUBTITLE_OLLAMA_MODEL` | `translategemma` | Ollama model tag, for example `translategemma:12b` |
| `SUBTITLE_OLLAMA_URL` | `http://localhost:11434/api/generate` | Ollama generate API endpoint |
| `SUBTITLE_WHISPER_MODEL` | `large-v3` | Faster-Whisper model size/name, for example `medium` or `small` to reduce resource use |
| `SUBTITLE_WHISPER_DEVICE` | `cpu` | Whisper device, such as `cpu` or a supported `cuda` setup |
| `SUBTITLE_WHISPER_COMPUTE_TYPE` | `int8` | Faster-Whisper compute type; compatible values depend on the selected device |
| `SUBTITLE_WHISPER_CPU_THREADS` | `12` | CPU threads used by Faster-Whisper |

Example for Windows PowerShell: use the 12B translator and a smaller Whisper model for a lower-memory transcription setup:

```powershell
ollama pull translategemma:12b
$env:SUBTITLE_OLLAMA_MODEL = "translategemma:12b"
$env:SUBTITLE_WHISPER_MODEL = "small"
uv run universaltranslator
```

The same configuration in Linux Bash uses `export`:

```bash
ollama pull translategemma:12b
export SUBTITLE_OLLAMA_MODEL=translategemma:12b
export SUBTITLE_WHISPER_MODEL=small
uv run universaltranslator
```

Environment variables set in a shell apply only to that session. For CUDA, install and verify compatible NVIDIA/CUDA dependencies separately; selecting CUDA in the installer or setting `SUBTITLE_WHISPER_DEVICE=cuda` does not install GPU support.

CLI mode does not import Tkinter and does not open windows. Transcription asks whether to use a local media path or a YouTube URL, then asks for an output path. Translation uses numbered language menus, then asks for input and output SRT paths. GUI mode uses file dialogs and language dropdowns, and requires Tkinter plus a desktop session.

## Ollama setup

Install [Ollama](https://ollama.com/download), then pull the default model:

```powershell
ollama pull translategemma
```

Confirm Ollama is running, then launch `uv run universaltranslator`. If Ollama uses a different host or port, set `SUBTITLE_OLLAMA_URL` to its `/api/generate` endpoint. If you use a remote Ollama host, subtitle text is sent to that host rather than staying on this computer.

## YouTube and permitted use

For YouTube, the app downloads audio to a temporary directory, transcribes it, and removes the temporary download after processing. Node.js must be installed and available as `node`. yt-dlp may retrieve its challenge-solving component from GitHub. Some videos may still be unavailable due to their access settings, location, or other restrictions; this tool does not bypass those restrictions. Only process content you own or are authorized to use, and follow applicable platform terms and laws.

## Privacy and files

- Local-file transcription and default local Ollama translation run on your computer.
- YouTube audio is downloaded temporarily; the generated SRT is saved where you choose.
- SRT translation sends subtitle text to the configured Ollama endpoint.
- Model files are stored by Faster-Whisper/Ollama, not in this repository.
- `.gitignore` excludes media, SRT outputs, virtual environments, caches, and build artifacts. Do not add private media or subtitles to Git.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `uv` is not recognized | Install uv, then open a new terminal so PATH refreshes |
| YouTube JavaScript-runtime warning | Install Node.js, confirm `node --version`, and run from a new terminal |
| YouTube challenge component cannot download | Check internet/GitHub access; YouTube extraction can change and may temporarily fail |
| Ollama connection refused | Start Ollama and verify the configured URL and port |
| Ollama says model not found | Run `ollama pull translategemma` or pull the exact configured variant |
| Whisper is too slow or runs out of memory | Select `small` or `medium`; this may reduce recognition quality |
| Translation quality is weak | Verify the source/target choices, try a larger TranslateGemma tag, and review the result |

## Verify the installation

```sh
uv sync --locked
uv run python -m py_compile app_config.py subtitles.py universaltranslator.py
```