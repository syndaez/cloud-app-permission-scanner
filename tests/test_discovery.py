from pathlib import Path

from cloud_app_permission_scanner.config import ScanConfig
from cloud_app_permission_scanner.discovery import ClassFileFinder


def test_discovery_uses_only_regex_filters(tmp_path):
    root = tmp_path / "scan-root"
    keep_dir = root / "com" / "example" / "keep"
    keep_dir.mkdir(parents=True)
    skip_dir = root / "com" / "example" / "generated"
    skip_dir.mkdir(parents=True)

    keep_file = keep_dir / "Keep.class"
    keep_file.write_bytes(b"keep")
    skip_file = skip_dir / "Skip.class"
    skip_file.write_bytes(b"skip")
    another_keep = root / "com" / "example" / "other.class"
    another_keep.write_bytes(b"other")

    config = ScanConfig(
        root=root,
        include_re=r".*com/example/.*",
        exclude_re=r".*generated.*",
    )
    finder = ClassFileFinder(config)

    assert finder.isEligible(root / "com" / "example" / "keep" / "Keep.class")
    assert not finder.isEligible(root / "com" / "example" / "generated" / "Skip.class")

    found = [path.name for path in finder.find()]

    assert found == ["Keep.class", "other.class"]
