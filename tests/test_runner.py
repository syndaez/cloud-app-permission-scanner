import json
from pathlib import Path

from cloud_app_permission_scanner import ScanConfig, run
from cloud_app_permission_scanner.runner import main
from tests.conftest import requires_jdk

EXPECTED_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "dynamodbAccess",
            "Effect": "Allow",
            "Action": ["dynamodb:GetItem", "dynamodb:PutItem"],
            "Resource": "*",
        },
        {
            "Sid": "logsAccess",
            "Effect": "Allow",
            "Action": ["logs:PutLogEvents"],
            "Resource": "*",
        },
        {
            "Sid": "sqsAccess",
            "Effect": "Allow",
            "Action": ["sqs:SendMessage"],
            "Resource": "*",
        },
        {
            "Sid": "S3BucketAccess",
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": ["arn:aws:s3:::*"],
        },
        {
            "Sid": "S3ObjectAccess",
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject"],
            "Resource": ["arn:aws:s3:::*/*"],
        },
    ],
}


def test_no_class_files_returns_2(tmp_path: Path) -> None:
    out = tmp_path / "policy.json"
    assert run(ScanConfig(root=tmp_path, output=out)) == 2
    assert not out.exists()


def test_no_sdk_references_writes_nothing(tmp_path: Path) -> None:
    (tmp_path / "A.class").write_bytes(b"\xca\xfe\xba\xbe java/lang/Object")
    out = tmp_path / "policy.json"
    assert run(ScanConfig(root=tmp_path, output=out)) == 0
    assert not out.exists()


@requires_jdk
def test_end_to_end_policy(compiled_app: Path, tmp_path: Path) -> None:
    out = tmp_path / "nested" / "policy.json"
    assert run(ScanConfig(root=compiled_app, output=out, jobs=2)) == 0
    assert json.loads(out.read_text(encoding="utf-8")) == EXPECTED_POLICY


@requires_jdk
def test_package_filter_limits_scan(compiled_app: Path, tmp_path: Path) -> None:
    out = tmp_path / "policy.json"
    config = ScanConfig(
        root=compiled_app, output=out, include_re=r".*com/example/logging.*"
    )
    assert run(config) == 0
    sids = [s["Sid"] for s in json.loads(out.read_text())["Statement"]]
    assert sids == ["logsAccess", "sqsAccess"]


@requires_jdk
def test_main_print_calls(compiled_app: Path, tmp_path: Path, capsys) -> None:
    out = tmp_path / "policy.json"
    code = main(["--root", str(compiled_app), "--out", str(out), "--print-calls"])
    assert code == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines == [
        "cloudwatchlogs\tCloudWatchLogsClient\tputLogEvents",
        "dynamodb\tDynamoDbClient\tgetItem",
        "dynamodb\tDynamoDbClient\tputItem",
        "s3\tS3Client\tgetObject",
        "s3\tS3Client\tlistObjectsV2",
        "s3\tS3Client\tputObject",
        "sqs\tSqsClient\tsendMessage",
    ]
