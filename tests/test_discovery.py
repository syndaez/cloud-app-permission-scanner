import re
from pathlib import Path

from cloud_app_permission_scanner.config import ScanConfig
from cloud_app_permission_scanner.discovery import ClassFileFinder


def make_tree(root: Path, rel_paths: list[str]) -> None:
    for rel in rel_paths:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"\xca\xfe\xba\xbe")


def found(root: Path, **kwargs) -> set[str]:
    finder = ClassFileFinder(ScanConfig(root=root, **kwargs))
    return {p.relative_to(root).as_posix() for p in finder.find()}


def test_finds_only_class_files(tmp_path: Path) -> None:
    make_tree(tmp_path, ["a/A.class", "a/B.java", "b/c/C.class", "README.md"])
    assert found(tmp_path) == {"a/A.class", "b/c/C.class"}


def test_exclude_re(tmp_path: Path) -> None:
    make_tree(tmp_path, ["main/A.class", "test/B.class"])
    assert found(tmp_path, exclude_re=r"/test/") == {"main/A.class"}


def test_include_re(tmp_path: Path) -> None:
    make_tree(tmp_path, ["target/classes/A.class", "other/B.class"])
    assert found(tmp_path, include_re=r"target/classes") == {"target/classes/A.class"}


def test_package_filter_with_regex(tmp_path: Path) -> None:
    make_tree(tmp_path, ["com/acme/A.class", "org/other/B.class"])
    assert found(tmp_path, include_re=r"com/acme") == {"com/acme/A.class"}


def test_none_filters_match_everything(tmp_path: Path) -> None:
    make_tree(tmp_path, ["A.class", "x/B.class"])
    assert found(tmp_path, include_re=None, exclude_re=None) == {
        "A.class",
        "x/B.class",
    }


def test_discovery_uses_only_regex_filters(tmp_path: Path) -> None:
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

    assert finder.is_eligible(root / "com" / "example" / "keep" / "Keep.class")
    assert not finder.is_eligible(root / "com" / "example" / "generated" / "Skip.class")
    assert finder.isEligible(root / "com" / "example" / "keep" / "Keep.class")

    found_names = [path.name for path in finder.find()]
    assert found_names == ["Keep.class", "other.class"]


def test_discovery_accepts_compiled_pattern(tmp_path: Path) -> None:
    make_tree(tmp_path, ["com/example/App.class", "com/example/Mock.class"])

    config = ScanConfig(
        root=tmp_path,
        include_re=re.compile(r"App\.class$"),
    )
    finder = ClassFileFinder(config)

    found_paths = [p.name for p in finder.find()]
    assert found_paths == ["App.class"]


def test_contains_sdk_reference(tmp_path: Path) -> None:
    hit = tmp_path / "Hit.class"
    miss = tmp_path / "Miss.class"
    hit.write_bytes(b"\x00software/amazon/awssdk/services/s3/S3Client\x00")
    miss.write_bytes(b"\x00java/lang/String\x00")
    assert ClassFileFinder.contains_sdk_reference(hit)
    assert not ClassFileFinder.contains_sdk_reference(miss)
    assert not ClassFileFinder.contains_sdk_reference(tmp_path / "Missing.class")
