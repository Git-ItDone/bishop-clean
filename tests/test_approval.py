from bishop.approval import ApprovalChoice, ApprovalPolicy
from bishop.safety import RiskTier, SafetyDecision


def test_approval_policy_remembers_allow_always():
    calls = {"count": 0}

    def approver(decision, action, context):
        calls["count"] += 1
        return ApprovalChoice.ALLOW_ALWAYS

    policy = ApprovalPolicy(approver)
    decision = SafetyDecision(RiskTier.CAUTION, "workspace-write", "write")

    assert policy.decide(decision, "write", "file") is True
    assert policy.decide(decision, "write", "file") is True
    assert calls["count"] == 1


def test_approval_policy_rejects_without_approver():
    policy = ApprovalPolicy()
    decision = SafetyDecision(RiskTier.DANGEROUS, "outside-workspace", "write")

    try:
        policy.decide(decision, "write", "file")
    except RuntimeError as exc:
        assert "no approver" in str(exc)
    else:
        raise AssertionError("expected missing approver to fail")

