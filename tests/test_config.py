from pathlib import Path

import pytest

from cloud_app_permission_scanner.config import ScanConfig


def test_from_cli_defaults() -> None:
    config = ScanConfig.from_cli([])
    assert config.root == Path(".")
    assert config.include_re is None
    assert config.exclude_re is None
    assert config.output == Path("permissions-policy.json")
    assert config.jobs >= 1
    assert not config.print_calls
    assert not config.debug


def test_from_cli_parses_arguments() -> None:
    config = ScanConfig.from_cli(
        [
            "--root",
            "build",
            "--include-re",
            "classes",
            "--exclude-re",
            "Test",
            "--jobs",
            "3",
            "--out",
            "out/policy.json",
            "--print-calls",
            "--debug",
        ]
    )
    assert config == ScanConfig(
        root=Path("build"),
        include_re="classes",
        exclude_re="Test",
        jobs=3,
        output=Path("out/policy.json"),
        print_calls=True,
        debug=True,
    )


def test_from_cli_empty_strings_disable_filters() -> None:
    config = ScanConfig.from_cli(["--include-re", "", "--exclude-re", ""])
    assert config.include_re is None
    assert config.exclude_re is None


def test_invalid_regex_raises_argparse_error() -> None:
    with pytest.raises(SystemExit) as exc_info:
        ScanConfig.from_cli(["--include-re", "["])
    assert exc_info.value.code == 2

    with pytest.raises(SystemExit) as exc_info:
        ScanConfig.from_cli(["--exclude-re", "("])
    assert exc_info.value.code == 2
