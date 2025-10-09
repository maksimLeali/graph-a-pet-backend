import argparse
import sys
from pathlib import Path
from yt_dlp import YoutubeDL

def on_progress(d):
    if d.get('status') == 'downloading':
        # Esempio: "42.3% 3.1MiB/7.4MiB ETA 00:12"
        p = d.get('_percent_str', '').strip()
        s = d.get('_speed_str', '').strip()
        eta = d.get('_eta_str', '').strip()
        sys.stdout.write(f"\rScaricando: {p}  Velocità: {s}  ETA: {eta}   ")
        sys.stdout.flush()
    elif d.get('status') == 'finished':
        print("\nDownload completato. Elaborazione post…")

def build_ydl_opts(args):
    outtmpl = str(Path(args.output_dir).expanduser() / args.output_template)

    # Se audio-only, scegli il miglior audio e converti a mp3 (o m4a) se richiesto
    if args.audio_only:
        postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": args.audio_format, "preferredquality": str(args.audio_quality)}]
        fmt = "bestaudio/best"
    else:
        # Miglior video+audio con fallback
        # bestvideo*+bestaudio/best garantisce qualità massima; puoi fissare max risoluzione con 'bestvideo[height<=1080]+bestaudio/best'
        fmt = args.format if args.format else "bestvideo*+bestaudio/best"
        postprocessors = [{"key": "FFmpegVideoRemuxer", "preferedformat": args.remux}] if args.remux else []

    ydl_opts = {
        "format": fmt,
        "merge_output_format": args.remux if args.remux else None,
        "outtmpl": outtmpl,
        "noplaylist": not args.playlist,
        "playliststart": args.playlist_start,
        "playlistend": args.playlist_end if args.playlist_end > 0 else None,
        "writesubtitles": args.subtitles,
        "writeautomaticsub": args.auto_subtitles,
        "subtitleslangs": args.sub_langs,
        "postprocessors": postprocessors,
        "progress_hooks": [on_progress],
        "quiet": False,
        "restrictfilenames": True,
        "concurrent_fragment_downloads": args.concurrent,
        "ratelimit": args.rate_limit,  # es. "2M"
        "cookiefile": args.cookies if args.cookies else None,
    }

    # Rimuovi chiavi None per pulizia
    return {k: v for k, v in ydl_opts.items() if v is not None}

def main():
    parser = argparse.ArgumentParser(description="Scarica video o audio da YouTube con yt-dlp.")
    parser.add_argument("url", help="URL video o playlist YouTube")
    parser.add_argument("-o", "--output-dir", default="downloads", help="Cartella di destinazione (default: downloads)")
    parser.add_argument("--output-template", default="%(title)s [%(id)s].%(ext)s",
                        help="Template filename yt-dlp (default: '%(title)s [%(id)s].%(ext)s')")
    parser.add_argument("-p", "--playlist", action="store_true", help="Abilita download dell’intera playlist")
    parser.add_argument("--playlist-start", type=int, default=1, help="Indice iniziale playlist (default: 1)")
    parser.add_argument("--playlist-end", type=int, default=0, help="Indice finale playlist (0 = fino alla fine)")

    # Video options
    parser.add_argument("-f", "--format", default=None,
                        help="Formato yt-dlp, es. 'bestvideo[height<=1080]+bestaudio/best'")
    parser.add_argument("--remux", choices=["mp4", "mkv", "webm"], default="mp4",
                        help="Formato contenitore finale per il merge (default: mp4)")

    # Audio-only options
    parser.add_argument("--audio-only", action="store_true", help="Scarica solo audio")
    parser.add_argument("--audio-format", choices=["mp3", "m4a", "wav", "flac"], default="mp3",
                        help="Codec output audio-only (default: mp3)")
    parser.add_argument("--audio-quality", type=int, default=320,
                        help="Qualità audio (kbps) per mp3/m4a dove applicabile (default: 320)")

    # Sottotitoli
    parser.add_argument("--subtitles", action="store_true", help="Scarica sottotitoli se disponibili")
    parser.add_argument("--auto-subtitles", action="store_true", help="Scarica sottotitoli auto-generati")
    parser.add_argument("--sub-langs", nargs="+", default=["it", "en"],
                        help="Lingue sottotitoli (default: it en)")

    # Affidabilità/performance
    parser.add_argument("--cookies", default=None, help="Percorso a file cookies.txt (opzionale)")
    parser.add_argument("--concurrent", type=int, default=4, help="Download frammenti in parallelo (default: 4)")
    parser.add_argument("--rate-limit", default=None, help="Limite banda, es. '2M' (opzionale)")

    args = parser.parse_args()
    Path(args.output_dir).expanduser().mkdir(parents=True, exist_ok=True)

    ydl_opts = build_ydl_opts(args)
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([args.url])
    except Exception as e:
        print(f"\nErrore: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()