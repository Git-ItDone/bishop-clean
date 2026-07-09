import json
from pathlib import Path

from bishop.audit import JsonlAuditSink
from bishop.safety import RiskTier, SafetyDecision


def test_jsonl_audit_sink_writes_entry(tmp_path: Path):
    path = tmp_path / "audit.jsonl"
    sink = JsonlAuditSink(path)
    decision = SafetyDecision(RiskTier.CAUTION, "workspace-write", "write file")

    entry = sink.record(
        tool="write_file",
        decision=decision,
        outcome="approved",
        workspace=tmp_path,
        details={"path": "file.txt"},
    )

    assert entry is not None
    row = json.loads(path.read_text(encoding="utf-8"))
    assert row["tool"] == "write_file"
    assert row["tier"] == "CAUTION"
    assert row["details"]["path"] == "file.txt"

