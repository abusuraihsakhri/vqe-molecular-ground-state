"""
Automated Pytest Test Suite for Vqe Molecular Ground State.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException, MAX_PHI_SCAN_LENGTH
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main, _validate_file_path


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_phi_guard_redaction():
    text = "Contact patient at 555-123-4567 or MRN-12345"
    redacted = PHIGuard.redact_phi(text)
    assert "555-123-4567" not in redacted
    assert "MRN-12345" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted


def test_phi_guard_long_input_rejected():
    """Ensure excessively long inputs are rejected (ReDoS guard)."""
    long_input = "A" * (MAX_PHI_SCAN_LENGTH + 1)
    with pytest.raises(SecurityException, match="exceeds maximum scan length"):
        PHIGuard.assert_no_phi(long_input)


def test_phi_guard_email_detection():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Send results to patient@hospital.com")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_metric_validation_rejects_nan():
    with pytest.raises(ValueError, match="NaN"):
        SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=float("nan"))


def test_metric_validation_rejects_infinity():
    with pytest.raises(ValueError, match="finite"):
        SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=float("inf"))


def test_metric_validation_rejects_out_of_bounds():
    with pytest.raises(ValueError, match="exceeds safety bounds"):
        SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=1e9)


def test_metric_validation_accepts_valid_range():
    p = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=25.0, secondary_metric=-5.0)
    assert p.primary_metric == 25.0
    assert p.secondary_metric == -5.0


def test_file_path_validation_rejects_traversal():
    with pytest.raises(ValueError, match="Invalid file path"):
        _validate_file_path("../../etc/passwd")


def test_file_path_validation_rejects_missing_file():
    with pytest.raises(FileNotFoundError):
        _validate_file_path("nonexistent_file.csv", must_exist=True)


def test_file_path_validation_accepts_valid_path():
    result = _validate_file_path("results.csv")
    assert result == "results.csv"


def test_batch_cli_with_sample_csv():
    """Test batch processing with the included sample.csv."""
    import tempfile
    import os
    sample = str(Path(__file__).parent.parent / "sample.csv")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        output_path = f.name
    try:
        exit_code = main(["batch", "-i", sample, "-o", output_path])
        assert exit_code == 0
        assert os.path.isfile(output_path)
        with open(output_path, 'r') as f:
            content = f.read()
            assert "overall_urgency" in content
    finally:
        os.unlink(output_path)


def test_batch_cli_missing_file_returns_error():
    """Test batch processing with a missing input file returns error code."""
    exit_code = main(["batch", "-i", "nonexistent.csv", "-o", "out.csv"])
    assert exit_code == 1
