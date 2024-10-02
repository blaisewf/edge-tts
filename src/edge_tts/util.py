import argparse
import asyncio
import sys
from io import TextIOWrapper
from typing import Any, TextIO, Union
from . import Communicate, SubMaker, list_voices


async def _print_voices(proxy: str) -> None:
    """Print all available voices, sorted by ShortName."""
    voices = sorted(await list_voices(proxy=proxy), key=lambda v: v["ShortName"])
    for idx, voice in enumerate(voices):
        if idx > 0:
            print()

        for key, value in voice.items():
            if key not in {
                "SuggestedCodec",
                "FriendlyName",
                "Status",
                "VoiceTag",
                "Name",
                "Locale",
            }:
                print(f"{'Name' if key == 'ShortName' else key}: {value}")


async def _run_tts(args: Any) -> None:
    """Run TTS and handle media and subtitle output."""
    if sys.stdin.isatty() and sys.stdout.isatty() and not args.write_media:
        print(
            "Warning: TTS output will be written to the terminal. "
            "Use --write-media to write to a file.\n"
            "Press Ctrl+C to cancel the operation. "
            "Press Enter to continue.",
            file=sys.stderr,
        )
        try:
            input()
        except KeyboardInterrupt:
            print("\nOperation canceled.", file=sys.stderr)
            return

    tts = Communicate(
        args.text,
        args.voice,
        proxy=args.proxy,
        rate=args.rate,
        volume=args.volume,
        pitch=args.pitch,
    )

    subs = SubMaker()
    audio_output = (
        open(args.write_media, "wb") if args.write_media else sys.stdout.buffer
    )

    async with audio_output:
        async for chunk in tts.stream():
            if chunk["type"] == "audio":
                audio_output.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                subs.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])

    if args.write_subtitles:
        with open(args.write_subtitles, "w", encoding="utf-8") as sub_file:
            sub_file.write(subs.generate_subs(args.words_in_cue))
    else:
        sys.stderr.write(subs.generate_subs(args.words_in_cue))


async def amain() -> None:
    """Parse arguments and run the appropriate TTS action."""
    parser = argparse.ArgumentParser(description="Microsoft Edge TTS")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-t", "--text", help="Text for TTS.")
    group.add_argument("-f", "--file", help="Read text for TTS from file.")
    group.add_argument(
        "-l",
        "--list-voices",
        action="store_true",
        help="List available voices and exit.",
    )

    parser.add_argument(
        "-v",
        "--voice",
        default="en-US-AriaNeural",
        help="TTS voice (default: en-US-AriaNeural).",
    )
    parser.add_argument("--rate", default="+0%", help="Set TTS rate (default: +0%).")
    parser.add_argument(
        "--volume", default="+0%", help="Set TTS volume (default: +0%)."
    )
    parser.add_argument(
        "--pitch", default="+0Hz", help="Set TTS pitch (default: +0Hz)."
    )
    parser.add_argument(
        "--words-in-cue",
        default=10,
        type=int,
        help="Number of words in subtitle cue (default: 10).",
    )
    parser.add_argument(
        "--write-media", help="Send media output to file instead of stdout."
    )
    parser.add_argument(
        "--write-subtitles", help="Send subtitle output to file instead of stderr."
    )
    parser.add_argument("--proxy", help="Use a proxy for TTS and voice list.")

    args = parser.parse_args()

    if args.list_voices:
        await _print_voices(proxy=args.proxy)
        sys.exit(0)

    if args.file:
        with open(args.file, "r", encoding="utf-8") as file:
            args.text = file.read()

    if args.text:
        await _run_tts(args)


def main() -> None:
    """Run the asynchronous main function."""
    asyncio.run(amain())


if __name__ == "__main__":
    main()
