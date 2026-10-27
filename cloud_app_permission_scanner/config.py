"""Scan configuration — immutable settings for a scanning run."""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ScanConfig:
    """Immutable configuration for a scanning run."""

    root: Path = Path(".")
    include_re: str | re.Pattern[str] | None = None
    exclude_re: str | re.Pattern[str] | None = None
    jobs: int = field(default_factory=lambda: max(1, os.cpu_count() or 4))
    output: Path = Path("permissions-policy.json")
    print_calls: bool = False
    debug: bool = False

    @classmethod
    def from_cli(cls, argv: list[str] | None = None) -> ScanConfig:
        """Build configuration from command-line arguments."""
        ap = argparse.ArgumentParser(
            description=(
                "Scan compiled .class files for AWS SDK v2 service client calls "
                "and generate an IAM permissions policy JSON."
            )
        )
        ap.add_argument("--root", default=".", help="Root directory to scan.")
        ap.add_argument(
            "--include-re",
            default=None,
            help=(
                "Regex for classfile paths to include. "
                "If set, only matching paths are scanned."
            ),
        )
        ap.add_argument(
            "--exclude-re",
            default=None,
            help="Regex for classfile paths to exclude.",
        )
        ap.add_argument(
            "--jobs",
            type=int,
            default=max(1, os.cpu_count() or 4),
            help="Parallel workers (threads).",
        )
        ap.add_argument(
            "--out", default="permissions-policy.json", help="Output policy file."
        )
        ap.add_argument(
            "--print-calls",
            action="store_true",
            help="Print discovered service/client/op list to stdout.",
        )
        ap.add_argument("--debug", action="store_true", help="Print progress info.")
        args = ap.parse_args(argv)

        flags = [
            ("--include-re", args.include_re),
            ("--exclude-re", args.exclude_re),
        ]
        for flag_name, val in flags:
            if val:
                try:
                    re.compile(val)
                except re.error as exc:
                    ap.error(f"Invalid regex for {flag_name}: {exc}")

        return cls(
            root=Path(args.root),
            include_re=args.include_re or None,
            exclude_re=args.exclude_re or None,
            jobs=args.jobs,
            output=Path(args.out),
            print_calls=args.print_calls,
            debug=args.debug,
        )
