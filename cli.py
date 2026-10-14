from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from i18n import SUPPORTED


@dataclass(frozen=True)
class Options:
    use_async: bool
    lang: str
    output_dir: Path
    verbose: bool

def build_parser(t) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yandex-ipod",
        description=t("program.description"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--async", dest="use_async", action="store_true",
        help=t("arg.mode"),
    )
    mode.add_argument(
        "--sync", dest="use_async", action="store_false",
        help=t("arg.mode"),
    )
    parser.set_defaults(use_async=False)

    parser.add_argument(
        "--lang", choices=SUPPORTED, default=None,
        help=t("arg.lang"),
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("tracks"),
        help=t("arg.output"),
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help=t("arg.verbose"),
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 1.1",
        help=t("arg.version"),
    )

    return parser

def parse_args(argv: list[str] | None = None) -> Options:
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--lang", choices=SUPPORTED, default=None)
    pre_args, _ = pre.parse_known_args(argv)

    from i18n import Translator, detect_lang
    t = Translator(detect_lang(pre_args.lang))

    parser = build_parser(t)
    ns = parser.parse_args(argv)

    lang = detect_lang(ns.lang)
    return Options(
        use_async=ns.use_async,
        lang=lang,
        output_dir=ns.output,
        verbose=ns.verbose,
    )