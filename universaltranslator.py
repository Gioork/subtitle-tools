import os
import json
import re
import tempfile
from pathlib import Path

from app_config import choose_interface, load_settings
import requests

SETTINGS = load_settings()
OLLAMA_MODEL = SETTINGS.get("SUBTITLE_OLLAMA_MODEL", "translategemma")
OLLAMA_URL = SETTINGS.get("SUBTITLE_OLLAMA_URL", "http://localhost:11434/api/generate")
LANGUAGES = (
    "Albanian",
    "Arabic",
    "Bengali",
    "Chinese (Simplified)",
    "Chinese (Traditional)",
    "Dutch",
    "English",
    "French",
    "German",
    "Greek",
    "Gujarati",
    "Hebrew",
    "Hindi",
    "Indonesian",
    "Italian",
    "Japanese",
    "Kannada",
    "Korean",
    "Malay",
    "Marathi",
    "Persian",
    "Polish",
    "Portuguese",
    "Punjabi",
    "Romanian",
    "Russian",
    "Serbian",
    "Spanish",
    "Swahili",
    "Tamil",
    "Telugu",
    "Thai",
    "Turkish",
    "Ukrainian",
    "Urdu",
    "Vietnamese",
)
LANGUAGE_CODES = {
    "Albanian": "sq",
    "Arabic": "ar",
    "Bengali": "bn",
    "Chinese (Simplified)": "zh-Hans",
    "Chinese (Traditional)": "zh-Hant",
    "Dutch": "nl",
    "English": "en",
    "French": "fr",
    "German": "de",
    "Greek": "el",
    "Gujarati": "gu",
    "Hebrew": "he",
    "Hindi": "hi",
    "Indonesian": "id",
    "Italian": "it",
    "Japanese": "ja",
    "Kannada": "kn",
    "Korean": "ko",
    "Malay": "ms",
    "Marathi": "mr",
    "Persian": "fa",
    "Polish": "pl",
    "Portuguese": "pt",
    "Punjabi": "pa",
    "Romanian": "ro",
    "Russian": "ru",
    "Serbian": "sr",
    "Spanish": "es",
    "Swahili": "sw",
    "Tamil": "ta",
    "Telugu": "te",
    "Thai": "th",
    "Turkish": "tr",
    "Ukrainian": "uk",
    "Urdu": "ur",
    "Vietnamese": "vi",
}


def parse_srt(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r"\n\s*\n", content.strip())
    parsed = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        index = lines[0].strip()
        timestamp = lines[1].strip()
        text = "\n".join(lines[2:]).strip()
        parsed.append({"index": index, "timestamp": timestamp, "text": text})
    return parsed


def translate_stream(text, source_language, target_language):
    prompt = (
        f"You are a professional {source_language} ({LANGUAGE_CODES[source_language]}) to "
        f"{target_language} ({LANGUAGE_CODES[target_language]}) translator. "
        f"Accurately convey the meaning and nuances of the original {source_language} text "
        f"while using natural {target_language} grammar and vocabulary. "
        f"Return only the {target_language} translation, without explanations or commentary. "
        f"Translate the following {source_language} text into {target_language}:\n\n\n"
        f"{text}"
    )

    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True},
        stream=True,
        timeout=120,
    )
    response.raise_for_status()

    translated_chunks = []
    for line in response.iter_lines():
        if not line:
            continue
        data = json.loads(line.decode("utf-8"))
        chunk = data.get("response", "")
        if chunk:
            print(chunk, end="", flush=True)
            translated_chunks.append(chunk)
        if data.get("done"):
            break
    print()
    return "".join(translated_chunks).strip()


def select_srt_files_gui(root, source_language, target_language):
    from tkinter import filedialog

    input_path = filedialog.askopenfilename(
        title=f"Seleziona i sottotitoli in {source_language}",
        filetypes=[("File sottotitoli SRT", "*.srt"), ("Tutti i file", "*.*")],
        parent=root,
    )
    if not input_path:
        return None

    output_path = filedialog.asksaveasfilename(
        title=f"Salva i sottotitoli in {target_language}",
        initialfile="subtitles_translated.srt",
        defaultextension=".srt",
        filetypes=[("File sottotitoli SRT", "*.srt"), ("Tutti i file", "*.*")],
        parent=root,
    )
    if not output_path:
        return None

    return input_path, output_path


def with_srt_suffix(path):
    output_path = Path(path).expanduser()
    if output_path.suffix.lower() != ".srt":
        output_path = output_path.with_suffix(".srt") if output_path.suffix else Path(f"{output_path}.srt")
    return str(output_path)


def select_srt_files_cli(source_language, target_language):
    while True:
        input_path = input(f"Input SRT ({source_language}) path, or blank to cancel: ").strip().strip("\"'")
        if not input_path:
            return None
        input_path = str(Path(input_path).expanduser())
        if Path(input_path).is_file():
            break
        print("File not found. Try again.")

    output_path = input(f"Output SRT ({target_language}) path: ").strip().strip("\"'")
    if not output_path:
        return None
    output_path = with_srt_suffix(output_path)
    if Path(input_path).resolve() == Path(output_path).resolve():
        print("The output path must be different from the input SRT.")
        return None
    if Path(output_path).exists():
        overwrite = input("Output file exists. Overwrite it? [y/N]: ").strip().lower()
        if overwrite not in {"y", "yes"}:
            return None
    return input_path, output_path


def select_language(language_role):
    print(f"\nSelect {language_role} language:")
    for number, language in enumerate(LANGUAGES, start=1):
        print(f"{number:2}. {language}")

    while True:
        choice = input("Enter the number of your choice: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(LANGUAGES):
            return LANGUAGES[int(choice) - 1]
        print(f"Choose a number from 1 to {len(LANGUAGES)}.")


def select_language_gui(root, language_role):
    from tkinter import StringVar, Toplevel, ttk

    dialog = Toplevel(root)
    dialog.title(f"Choose {language_role} language")
    dialog.transient(root)
    dialog.resizable(False, False)

    selected_language = StringVar(dialog, value=LANGUAGES[0])
    result = {"language": None}
    ttk.Label(dialog, text=f"Choose {language_role} language:").pack(padx=16, pady=(16, 6))
    ttk.Combobox(
        dialog,
        textvariable=selected_language,
        values=LANGUAGES,
        state="readonly",
        width=28,
    ).pack(padx=16, pady=6)

    buttons = ttk.Frame(dialog)
    buttons.pack(padx=16, pady=(6, 16))
    ttk.Button(
        buttons,
        text="Cancel",
        command=dialog.destroy,
    ).pack(side="right", padx=(6, 0))

    def accept():
        result["language"] = selected_language.get()
        dialog.destroy()

    ttk.Button(buttons, text="Select", command=accept).pack(side="right")
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    dialog.grab_set()
    root.wait_window(dialog)
    return result["language"]


def main(interface=None):
    interface = interface or choose_interface()
    if interface == "gui":
        from tkinter import Tk

        root = Tk()
        root.withdraw()
        try:
            source_language = select_language_gui(root, "source")
            if source_language is None:
                print("Language selection cancelled.")
                return
            target_language = select_language_gui(root, "target")
            if target_language is None:
                print("Language selection cancelled.")
                return
            selected_files = select_srt_files_gui(root, source_language, target_language)
        finally:
            root.destroy()
    else:
        source_language = select_language("source")
        target_language = select_language("target")
        selected_files = select_srt_files_cli(source_language, target_language)

    if selected_files is None:
        print("Selezione dei file annullata.")
        return

    input_path, output_path = selected_files
    if Path(input_path).resolve() == Path(output_path).resolve():
        print("The output path must be different from the input SRT.")
        return

    blocks = parse_srt(input_path)
    if not blocks:
        raise ValueError(f"No valid subtitle blocks found in {input_path}")

    total = len(blocks)
    print(f"\nTranslating from {source_language} to {target_language}.")
    print(f"Blocchi da tradurre: {total}\n")

    destination = Path(output_path)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            for index, block in enumerate(blocks, start=1):
                print(f"--- [{index}/{total}] originale: {block['text']} ---")
                translated = translate_stream(block["text"], source_language, target_language)

                output.write(f"{block['index']}\n")
                output.write(f"{block['timestamp']}\n")
                output.write(f"{translated}\n\n")
                output.flush()

                print(f"--- [{index}/{total}] tradotto ---\n")

        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    print(f"\nCompletato: {output_path}")


if __name__ == "__main__":
    main()