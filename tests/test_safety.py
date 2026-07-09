from pathlib import Path

from bishop.safety import RiskTier, classify_command, classify_write, is_protected_path


def test_classify_safe_command():
    assert classify_command("pytest -q").tier is RiskTier.SAFE


def test_classify_blocked_command():
    assert classify_command("rm -rf /").tier is RiskTier.BLOCKED


def test_classify_dangerous_command():
    assert classify_command("git reset --hard HEAD").tier is RiskTier.DANGEROUS


def test_classify_caution_command():
    assert classify_command("git status").tier is RiskTier.CAUTION


def test_protected_secret_path():
    protected, reason = is_protected_path(Path.home() / ".ssh" / "id_rsa")

    assert protected
    assert reason == "user-secret-path"


def test_classify_workspace_write(tmp_path: Path):
    decision = classify_write(
        tmp_path / "new.txt",
        tmp_path,
        existing_bytes=None,
        new_bytes=10,
        mode="overwrite",
    )

    assert decision.tier is RiskTier.CAUTION


def test_classify_outside_write(tmp_path: Path):
    decision = classify_write(
        tmp_path.parent / "outside.txt",
        tmp_path,
        existing_bytes=None,
        new_bytes=10,
        mode="overwrite",
    )

    assert decision.tier is RiskTier.DANGEROUS

