"""Command line interface.

Exit codes
----------
0  success / verification PASS
1  verification FAIL, or the captured command failed (evidence is still written)
2  verification INCONCLUSIVE
3  usage error, invalid manifest, or capture could not be completed
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sciproof import __version__
from sciproof.capture import DEFAULT_ATOL, DEFAULT_MAX_LOG_BYTES, DEFAULT_RTOL, capture
from sciproof.errors import ConfirmationRequired, SciProofError
from sciproof.inspect_manifest import inspect_file
from sciproof.textutil import safe_text
from sciproof.verify import (
    DEFAULT_RERUN_TIMEOUT_SECONDS,
    Status,
    format_report,
    format_report_json,
    verify,
)

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_INCONCLUSIVE = 2
EXIT_ERROR = 3

_STATUS_EXIT = {
    Status.PASS: EXIT_OK,
    Status.FAIL: EXIT_FAIL,
    Status.INCONCLUSIVE: EXIT_INCONCLUSIVE,
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sciproof",
        description="Record computational experiments and create verifiable evidence for them.",
    )
    parser.add_argument("--version", action="version", version=f"sciproof {__version__}")
    sub = parser.add_subparsers(dest="command_name", required=True)

    cap = sub.add_parser(
        "capture",
        help="run a command once and record evidence",
        description=(
            "Run COMMAND once in the current directory and write NAME.sciproof.json. "
            "Everything after '--' is the command (it is not run through a shell)."
        ),
    )
    cap.add_argument("--name", required=True, help="experiment name (also names the manifest)")
    cap.add_argument(
        "--input",
        action="append",
        default=[],
        metavar="PATH",
        help="declare an input file or directory (hashed before and after the run); repeatable",
    )
    cap.add_argument(
        "--output",
        action="append",
        default=[],
        metavar="PATH",
        help="declare an output file or directory compared by exact hash; repeatable",
    )
    cap.add_argument(
        "--output-numeric",
        action="append",
        default=[],
        metavar="PATH",
        help="declare a .json/.csv output compared with a numeric tolerance; repeatable",
    )
    cap.add_argument(
        "--rtol",
        type=float,
        default=DEFAULT_RTOL,
        help=f"relative tolerance for numeric outputs (default {DEFAULT_RTOL})",
    )
    cap.add_argument(
        "--atol",
        type=float,
        default=DEFAULT_ATOL,
        help=f"absolute tolerance for numeric outputs (default {DEFAULT_ATOL})",
    )
    cap.add_argument(
        "--timeout",
        type=float,
        default=None,
        metavar="SECONDS",
        help="stop the command after this many seconds (no evidence is written)",
    )
    cap.add_argument(
        "--max-log-bytes",
        type=int,
        default=DEFAULT_MAX_LOG_BYTES,
        help="keep at most this many bytes of stdout and of stderr in the manifest",
    )
    cap.add_argument("--force", action="store_true", help="overwrite an existing manifest")
    cap.add_argument(
        "--allow-nonzero",
        action="store_true",
        help="exit with status 0 even if the command failed (evidence is written either way)",
    )
    cap.add_argument(
        "cmd", nargs=argparse.REMAINDER, metavar="-- COMMAND [ARGS...]", help="the command to run"
    )

    ver = sub.add_parser(
        "verify",
        help="check a manifest (integrity by default, re-execution only with --rerun)",
    )
    ver.add_argument("manifest", type=Path)
    ver.add_argument(
        "--rerun",
        action="store_true",
        help="EXECUTE the recorded command again and compare results "
        "(runs arbitrary code with your permissions)",
    )
    ver.add_argument(
        "--yes", action="store_true", help="do not ask for confirmation before --rerun"
    )
    ver.add_argument(
        "--strict-env",
        action="store_true",
        help="with --rerun: report INCONCLUSIVE if the environment differs",
    )
    ver.add_argument(
        "--clean-env",
        action="store_true",
        help="with --rerun: give the command only a minimal environment (PATH, temp "
        "directories, numerics-related variables) instead of all of yours, including credentials",
    )
    ver.add_argument(
        "--pass-env",
        action="append",
        default=[],
        metavar="NAME",
        help="with --clean-env: also pass this environment variable; repeatable",
    )
    ver.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_RERUN_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help="stop the rerun after this many seconds (default %(default)s)",
    )

    ver.add_argument(
        "--json",
        action="store_true",
        help="print the report as one JSON object (exit codes are unchanged)",
    )

    ins = sub.add_parser("inspect", help="show a readable summary; never executes anything")
    ins.add_argument("manifest", type=Path)
    return parser


def _confirm(prompt: str) -> bool:
    if not sys.stdin.isatty():
        raise ConfirmationRequired(
            "refusing to execute the recorded command: no terminal to ask for confirmation; "
            "re-run with --yes after reading the command (see 'sciproof inspect')"
        )
    print(prompt, file=sys.stderr)  # stderr keeps stdout clean for --json
    answer = input("\nExecute this command? Type 'yes' to continue: ")
    return answer.strip().lower() == "yes"


def _run_capture(args: argparse.Namespace) -> int:
    command = list(args.cmd)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SciProofError(
            "no command given; usage: sciproof capture --name NAME [options] -- COMMAND"
        )
    result = capture(
        name=args.name,
        argv=command,
        base=Path.cwd(),
        inputs=args.input,
        outputs=args.output,
        numeric_outputs=args.output_numeric,
        rtol=args.rtol,
        atol=args.atol,
        timeout=args.timeout,
        max_log_bytes=args.max_log_bytes,
        force=args.force,
    )
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    manifest = result.manifest
    print(f"Evidence written to {result.manifest_path.name}")
    print(f"  command exit code: {result.exit_code}")
    print(f"  inputs recorded:   {len(manifest['inputs'])}")
    print(f"  outputs recorded:  {len(manifest['outputs'])}")
    print(
        "Note: stdout/stderr are stored in the manifest; check them for secrets before sharing it."
    )
    if result.exit_code != 0:
        print(
            f"The command failed (exit code {result.exit_code}); the failure was recorded.",
            file=sys.stderr,
        )
        return EXIT_OK if args.allow_nonzero else EXIT_FAIL
    return EXIT_OK


def _run_verify(args: argparse.Namespace) -> int:
    report = verify(
        args.manifest,
        rerun=args.rerun,
        assume_yes=args.yes,
        strict_env=args.strict_env,
        timeout=args.timeout,
        confirm=_confirm if args.rerun and not args.yes else None,
        clean_env=args.clean_env,
        pass_env=args.pass_env,
    )
    print(format_report_json(report) if args.json else format_report(report))
    return _STATUS_EXIT[report.status]


def _make_output_robust() -> None:
    """Never crash because the terminal cannot encode a character from a manifest or a log.

    Captured stdout/stderr and file names can contain any character, while a console may use
    a narrow encoding (for example cp1252 on Windows). Unencodable characters are printed as
    escapes (``\u2713``) instead of raising ``UnicodeEncodeError``.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="backslashreplace")


def main(argv: list[str] | None = None) -> int:
    _make_output_robust()
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command_name == "capture":
            return _run_capture(args)
        if args.command_name == "verify":
            return _run_verify(args)
        print(inspect_file(args.manifest))
        return EXIT_OK
    except SciProofError as exc:
        print(f"error: {safe_text(str(exc), 2000)}", file=sys.stderr)
        return EXIT_ERROR
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return EXIT_ERROR
    except EOFError:
        print("error: no confirmation received", file=sys.stderr)
        return EXIT_ERROR
