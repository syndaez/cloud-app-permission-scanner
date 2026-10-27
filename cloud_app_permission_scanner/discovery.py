"""File discovery — walk the directory tree and filter .class files."""

from __future__ import annotations

import os
import re
from pathlib import Path

from cloud_app_permission_scanner.config import ScanConfig
from cloud_app_permission_scanner.constants import AWS_SDK_NEEDLE


class ClassFileFinder:
    """Walks a directory tree and yields matching ``.class`` files."""

    def __init__(self, config: ScanConfig) -> None:
        self._root = config.root
        self._include_re = re.compile(config.include_re) if config.include_re else None
        self._exclude_re = re.compile(config.exclude_re) if config.exclude_re else None

    def matches_include(self, path: str | Path) -> bool:
        """Return whether the path matches the include regex, if configured."""
        if self._include_re is None:
            return True
        return bool(self._include_re.search(Path(path).as_posix()))

    def matches_exclude(self, path: str | Path) -> bool:
        """Return whether the path matches the exclude regex."""
        if self._exclude_re is None:
            return False
        return bool(self._exclude_re.search(Path(path).as_posix()))

    # Backward-compatibility aliases
    include_re = matches_include
    exclude_re = matches_exclude

    def is_eligible(self, path: str | Path) -> bool:
        """Return whether the path should be processed."""
        return self.matches_include(path) and not self.matches_exclude(path)

    # Convenience alias
    isEligible = is_eligible

    def find(self) -> list[Path]:
        """Return all ``.class`` files matching the configured filters."""
        results: list[Path] = []
        for dirpath, _, filenames in os.walk(self._root):
            for fn in filenames:
                if not fn.endswith(".class"):
                    continue
                full = os.path.join(dirpath, fn)
                if not self.is_eligible(full):
                    continue
                results.append(Path(full))
        return sorted(results, key=lambda path: str(path))

    @staticmethod
    def contains_sdk_reference(path: Path) -> bool:
        """Fast binary check: does the classfile mention the SDK services prefix?"""
        try:
            return AWS_SDK_NEEDLE in path.read_bytes()
        except OSError:
            return False
