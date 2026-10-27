import os
import tempfile
from pathlib import Path

from app_config import choose_interface, load_settings
from faster_whisper import WhisperModel
import yt_dlp

SETTINGS = load_settings()
WHISPER_MODEL = SETTINGS.get("SUBTITLE_WHISPER_MODEL", "large-v3")
WHISPER_DEVICE = SETTINGS.get("SUBTITLE_WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = SETTINGS.get("SUBTITLE_WHISPER_COMPUTE_TYPE", "int8")
WHISPER_CPU_THREADS = int(SETTINGS.get("SUBTITLE_WHISPER_CPU_THREADS", "12"))


def srt_time(seconds):
    ms = int(round(seconds * 1000))
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def select_audio_source_gui(root):
    from tkinter import filedialog, messagebox, simpledialog

    use_youtube = messagebox.askyesno(
        "Sorgente audio",
        "Vuoi creare i sottotitoli da un URL YouTube?\n"
        "Scegli No per selezionare un file audio o video locale.",
        parent=root,
    )
    if use_youtube:
        url = simpledialog.askstring("URL YouTube", "Inserisci l'URL del video:", parent=root)
        if not url or not url.strip():
            return None
        return "youtube", url.strip()

    audio_file = filedialog.askopenfilename(
        title="Seleziona il file audio o video",
        filetypes=[
            ("Audio e video", "*.wav *.mp3 *.m4a *.aac *.flac *.ogg *.wma *.mp4"),
            ("Tutti i file", "*.*"),
        ],
        parent=root,
    )
    if not audio_file:
        return None
    return "file", audio_file


def select_audio_source_cli():
    while True:
        print("\nChoose audio source:")
        print("1. Local audio/video file")
        print("2. YouTube URL")
        print("0. Cancel")
        choice = input("Choice: ").strip()
        if choice == "0":
            return None
        if choice == "1":
            audio_file = input("Audio/video file path: ").strip().strip("\"'")
            audio_file = str(Path(audio_file).expanduser())
            if Path(audio_file).is_file():
                return "file", audio_file
            print("File not found. Try again.")
        elif choice == "2":
            url = input("YouTube URL: ").strip()
            if url:
                return "youtube", url
            print("URL cannot be empty.")
        else:
            print("Choose 0, 1, or 2.")


def select_output_cli():
    output_file = input("SRT output path: ").strip().strip("\"'")
    if not output_file:
        return None
    output_path = Path(output_file).expanduser()
    if output_path.suffix.lower() != ".srt":
        output_path = output_path.with_suffix(".srt") if output_path.suffix else Path(f"{output_path}.srt")
    return str(output_path)


def download_youtube_audio(url, output_directory):
    output_template = str(Path(output_directory) / "%(id)s.%(ext)s")
    options = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "js_runtimes": {"node": {}},
        "remote_components": {"ejs:github"},
    }
    with yt_dlp.YoutubeDL(options) as downloader:
        video_info = downloader.extract_info(url, download=True)
        return downloader.prepare_filename(video_info)


def transcribe_to_srt(audio_file, output_file):
    model = WhisperModel(
        WHISPER_MODEL,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE_TYPE,
        cpu_threads=WHISPER_CPU_THREADS,
    )
    segments, info = model.transcribe(audio_file, beam_size=5, vad_filter=True)

    print(f"Lingua rilevata: {info.language} (probabilità: {info.language_probability:.2f})")
    segments = list(segments)
    print(f"Segmenti trovati: {len(segments)}")

    if not segments:
        print("ATTENZIONE: nessun segmento trovato. Controlla il file audio o disattiva vad_filter.")

    with open(output_file, "w", encoding="utf-8") as output:
        subtitle_number = 1
        for segment in segments:
            transcribed_text = segment.text.strip()
            if not transcribed_text:
                continue
            output.write(f"{subtitle_number}\n")
            output.write(f"{srt_time(segment.start)} --> {srt_time(segment.end)}\n")
            output.write(f"{transcribed_text}\n\n")
            print(
                f"[{subtitle_number}] {srt_time(segment.start)} --> "
                f"{srt_time(segment.end)}: {transcribed_text}"
            )
            subtitle_number += 1

    print(f"\nCreato: {output_file} con {subtitle_number - 1} sottotitoli")


def main(interface=None):
    interface = interface or choose_interface()
    if interface == "gui":
        from tkinter import Tk, filedialog

        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            source = select_audio_source_gui(root)
            if source is None:
                print("Selezione della sorgente annullata.")
                return

            output_file = filedialog.asksaveasfilename(
                title="Scegli dove salvare i sottotitoli",
                defaultextension=".srt",
                filetypes=[("File sottotitoli SRT", "*.srt"), ("Tutti i file", "*.*")],
                parent=root,
            )
        finally:
            root.destroy()
    else:
        source = select_audio_source_cli()
        if source is None:
            print("Selezione della sorgente annullata.")
            return
        output_file = select_output_cli()

    if not output_file:
        print("Selezione del file di output annullata.")
        return

    source_type, source_value = source
    if source_type == "youtube":
        with tempfile.TemporaryDirectory(prefix="subtitles_audio_") as temporary_directory:
            audio_file = download_youtube_audio(source_value, temporary_directory)
            transcribe_to_srt(audio_file, output_file)
    else:
        transcribe_to_srt(source_value, output_file)


if __name__ == "__main__":
    main()