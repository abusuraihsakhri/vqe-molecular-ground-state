"""
FastAPI REST API Server for Vqe Molecular Ground State.
"""
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import Field
from vqe_ground_state.variational import solve_single_qubit
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Vqe Molecular Ground State API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


@app.exception_handler(SecurityException)
async def handle_phi_block(request: Request, exc: SecurityException):
    return JSONResponse(status_code=400, content={"detail": "Sensitive identifier or oversized field rejected"})


class VQERequest(BaseModel):
    offset: float = Field(default=-1.0, ge=-1e6, le=1e6, allow_inf_nan=False)
    z: float = Field(default=0.5, ge=-1e6, le=1e6, allow_inf_nan=False)
    x: float = Field(default=0.25, ge=-1e6, le=1e6, allow_inf_nan=False)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path(__file__).resolve().parent.parent / "web" / "index.html")


@app.get("/app.mjs", include_in_schema=False)
def web_app():
    return FileResponse(Path(__file__).resolve().parent.parent / "web" / "app.mjs", media_type="text/javascript")


@app.get("/core.mjs", include_in_schema=False)
def web_core():
    return FileResponse(Path(__file__).resolve().parent.parent / "web" / "core.mjs", media_type="text/javascript")


@app.post("/api/vqe")
def api_vqe(req: VQERequest):
    return solve_single_qubit(req.offset, req.z, req.x).to_dict()


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "vqe-molecular-ground-state", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException:
        raise HTTPException(status_code=400, detail="Sensitive identifier or oversized field rejected")


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
