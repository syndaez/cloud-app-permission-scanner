"""Parallel scanner — orchestrates discovery and extraction across class files."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from cloud_app_permission_scanner.config import ScanConfig
from cloud_app_permission_scanner.discovery import ClassFileFinder
from cloud_app_permission_scanner.extractor import JavapExtractor
from cloud_app_permission_scanner.models import ScanResult

logger = logging.getLogger(__name__)


class ClassScanner:
    """Orchestrates parallel scanning of class files."""

    def __init__(self, config: ScanConfig) -> None:
        self._config = config
        self._finder = ClassFileFinder(config)
        self._extractor = JavapExtractor()

    def scan(self) -> ScanResult:
        """Run the full discovery → prefilter → extract pipeline."""
        candidates = self._finder.find()
        result = ScanResult(candidates_count=len(candidates))

        if not candidates:
            logger.error(
                "No .class files matched filters. "
                "Adjust --root / --include-re / --exclude-re."
            )
            return result

        work = [cf for cf in candidates if ClassFileFinder.contains_sdk_reference(cf)]
        result.scanned_count = len(work)

        if self._config.debug:
            logger.info(
                "Candidates: %d; prefilter hits: %d", len(candidates), len(work)
            )

        if not work:
            logger.info("No classfiles contained AWS SDK v2 services references.")
            return result

        self._scan_parallel(work, result)
        return result

    def _scan_parallel(self, work: list[Path], result: ScanResult) -> None:
        with ThreadPoolExecutor(max_workers=self._config.jobs) as executor:
            future_to_path = {
                executor.submit(self._extractor.disassemble, cf): cf for cf in work
            }
            for future in as_completed(future_to_path):
                classfile = future_to_path[future]
                try:
                    javap_output = future.result()
                    result.calls |= self._extractor.extract_calls(javap_output)
                except Exception as exc:
                    result.failure_count += 1
                    logger.warning("Failed to scan %s: %s", classfile, exc)
