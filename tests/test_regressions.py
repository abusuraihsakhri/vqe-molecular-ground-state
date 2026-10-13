"""Regression coverage for audit signatures, backend endpoints, and CLI paths."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agents.base import AuditTrail, PHIGuard, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.api import app
from cli import _validate_file_path
from vqe_ground_state.cli import main as vqe_cli


def test_audit_detects_field_tampering():
    trail = AuditTrail(secret_key="test-key-for-signatures")
    trail.log("supervisor", "tier", "EVENT", {"status": "ok"})
    trail.log("supervisor", "tier", "EVENT", {"status": "ok2"})
    assert trail.verify_integrity()
    snapshot = trail.get_trail()
    snapshot[0]["event_type"] = "REPLACED"
    assert trail.verify_integrity(), "external snapshot must not mutate the ledger"
    trail.logs[0]["event_type"] = "REPLACED"
    assert not trail.verify_integrity(), "signed field tampering must be detected"


def test_audit_detects_hash_tampering():
    trail = AuditTrail(secret_key="test-key-for-signatures")
    trail.log("supervisor", "tier", "EVENT", {"status": "ok"})
    trail.logs[0]["current_hash"] = "0" * 64
    assert not trail.verify_integrity()


def test_supervisor_rejects_phi_inside_attributes():
    payload = SystemTaskPayload(task_id="SAFE-ID", target_identifier="SAFE-TARGET",
                                primary_metric=1.0, attributes={"comment": "MRN-12345"})
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


def test_path_check_accepts_absolute_temp_path(tmp_path):
    path = tmp_path / "input.csv"
    path.write_text("task_id,target_identifier,primary_metric\nX,Y,1\n")
    assert _validate_file_path(str(path), must_exist=True) == str(path)


@pytest.mark.parametrize("path", ["../out.csv", "a/../b.csv", "..\\back.csv", ""])
def test_path_check_rejects_traversal(path):
    with pytest.raises(ValueError):
        _validate_file_path(path)


def test_vqe_cli_entry(capsys):
    assert vqe_cli(["solve", "--offset", "-1", "--z", "0.5", "--x", "0.25"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["converged"]
    assert result["absolute_error"] < 1e-8
    assert vqe_cli(["solve", "--z", "nan"]) == 2


def test_web_routes_and_numerical_endpoint():
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert "Variational Quantum Eigensolver" in client.get("/").text
    assert client.get("/app.mjs").status_code == 200
    assert client.get("/core.mjs").status_code == 200
    result = client.post("/api/vqe", json={"offset": -1, "z": 0.5, "x": 0.25})
    assert result.status_code == 200
    assert result.json()["converged"]
    assert client.post("/api/vqe", json={"z": 1e20}).status_code == 422


def test_api_rejects_phi_without_server_error():
    client = TestClient(app)
    response = client.post("/api/audit", json={
        "task_id": "A", "target_identifier": "B", "primary_metric": 2,
        "attributes": {"notes": "MRN-12345"}
    })
    assert response.status_code == 400
    assert "MRN" not in response.text
