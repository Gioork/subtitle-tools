#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

if [[ "$(uname -s)" != Linux* ]]; then
    printf 'This setup script is for Linux. Use setup.ps1 on Windows.\n' >&2
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    printf 'uv is not installed. Install it from https://docs.astral.sh/uv/ and reopen your terminal.\n' >&2
    exit 1
fi

python_bin="$(command -v python3 || true)"
if [[ -z "$python_bin" ]]; then
    printf 'Python 3 is not installed. Install Python 3.11, 3.12, or 3.13 first.\n' >&2
    exit 1
fi

config_value() {
    local name="$1" default="$2" line value
    if [[ -f .env ]]; then
        while IFS= read -r line; do
            if [[ "$line" == "$name="* ]]; then
                value="${line#*=}"
                value="${value%$'\r'}"
                value="${value#\"}"
                value="${value%\"}"
                value="${value#\'}"
                value="${value%\'}"
                printf '%s' "$value"
                return
            fi
        done < .env
    fi
    printf '%s' "$default"
}

uv sync --python "$python_bin"

saved_interface="$(config_value SUBTITLE_INTERFACE gui)"
if [[ "$saved_interface" == cli ]]; then interface_default=2; else interface_default=1; fi
read -r -p "Default interface: 1 GUI dialogs, 2 CLI only [$interface_default]: " interface_choice
case "${interface_choice:-$interface_default}" in
    2|cli|CLI) interface=cli ;;
    *) interface=gui ;;
esac

printf '\nChoose the default Whisper model:\n'
printf '1. large-v3 (best quality, more resources)\n2. medium\n3. small\n4. tiny (fastest, lower quality)\n'
saved_model="$(config_value SUBTITLE_WHISPER_MODEL large-v3)"
case "$saved_model" in
    medium) model_default=2 ;;
    small) model_default=3 ;;
    tiny) model_default=4 ;;
    *) model_default=1 ;;
esac
read -r -p "Whisper model [$model_default]: " model_choice
case "${model_choice:-$model_default}" in
    2) whisper_model=medium ;;
    3) whisper_model=small ;;
    4) whisper_model=tiny ;;
    *) whisper_model=large-v3 ;;
esac

saved_device="$(config_value SUBTITLE_WHISPER_DEVICE cpu)"
if [[ "$saved_device" == cuda ]]; then device_default=2; else device_default=1; fi
read -r -p "Whisper device: 1 CPU/int8, 2 CUDA/float16 [$device_default]: " device_choice
if [[ "${device_choice:-$device_default}" == 2 ]]; then
    whisper_device=cuda
    compute_type=float16
else
    whisper_device=cpu
    compute_type=int8
fi

saved_threads="$(config_value SUBTITLE_WHISPER_CPU_THREADS 12)"
read -r -p "Whisper CPU threads [$saved_threads]: " cpu_threads
cpu_threads="${cpu_threads:-$saved_threads}"
if [[ ! "$cpu_threads" =~ ^[1-9][0-9]*$ ]]; then
    printf 'Whisper CPU threads must be a positive integer.\n' >&2
    exit 1
fi

saved_ollama_model="$(config_value SUBTITLE_OLLAMA_MODEL translategemma)"
read -r -p "Ollama model [$saved_ollama_model]: " ollama_model
ollama_model="${ollama_model:-$saved_ollama_model}"
saved_ollama_url="$(config_value SUBTITLE_OLLAMA_URL http://localhost:11434/api/generate)"
read -r -p "Ollama generate URL [$saved_ollama_url]: " ollama_url
ollama_url="${ollama_url:-$saved_ollama_url}"

if [[ "$interface" == gui ]] && ! "$python_bin" -c 'import tkinter' >/dev/null 2>&1; then
    printf 'Tkinter is missing from %s. Install your distribution\047s Tk package, or rerun setup and choose CLI only.\n' "$python_bin" >&2
    exit 1
fi

read -r -p 'Save these choices in .env for future runs? [y/N]: ' save_settings
export SUBTITLE_INTERFACE="$interface"
export SUBTITLE_WHISPER_MODEL="$whisper_model"
export SUBTITLE_WHISPER_DEVICE="$whisper_device"
export SUBTITLE_WHISPER_COMPUTE_TYPE="$compute_type"
export SUBTITLE_WHISPER_CPU_THREADS="$cpu_threads"
export SUBTITLE_OLLAMA_MODEL="$ollama_model"
export SUBTITLE_OLLAMA_URL="$ollama_url"

if [[ "${save_settings,,}" == y || "${save_settings,,}" == yes ]]; then
    printf 'SUBTITLE_INTERFACE=%s\nSUBTITLE_WHISPER_MODEL=%s\nSUBTITLE_WHISPER_DEVICE=%s\nSUBTITLE_WHISPER_COMPUTE_TYPE=%s\nSUBTITLE_WHISPER_CPU_THREADS=%s\nSUBTITLE_OLLAMA_MODEL=%s\nSUBTITLE_OLLAMA_URL=%s\n' \
        "$interface" "$whisper_model" "$whisper_device" "$compute_type" "$cpu_threads" "$ollama_model" "$ollama_url" > .env
    chmod 600 .env
    printf '\nConfiguration saved to .env (ignored by Git).\n'
else
    printf '\nChoices apply only to this setup session; any existing .env was left unchanged.\n'
fi

printf '\nEnvironment ready. Choose a tool to run:\n'
printf '1. Transcribe local audio/video or a YouTube URL\n'
printf '2. Translate an SRT with Universal Translator\n'
printf 'Press Enter to finish setup only.\n'
read -r -p 'Choice: ' choice

case "$choice" in
    1) uv run subtitle-transcribe ;;
    2) uv run universaltranslator ;;
    *) printf 'Setup complete. Run this script again or use the commands in README.md.\n' ;;
esac