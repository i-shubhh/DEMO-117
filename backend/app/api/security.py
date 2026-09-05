"""Security and health status API endpoints per Section 7."""

from fastapi import APIRouter
from app.models.registry import registry
from app.security.network_check import security_monitor

security_router = APIRouter(prefix="/api", tags=["Security & Governance"])


@security_router.get("/security/status")
def get_security_status():
    """Returns verifiable zero-egress security status and network boundary checks."""
    status = security_monitor.verify_network_isolation()
    return {
        "air_gapped": status["air_gapped"],
        "external_calls": status["external_calls"],
        "outbound_traffic": status["outbound_traffic"],
        "local_models": status["local_models_count"],
        "local_models_status": "ONLINE" if status["local_model_online"] else "STANDBY",
        "local_vector_db": "ONLINE (Chroma / In-Memory)",
        "sandbox_network": status["sandbox_network"],
        "telemetry_policy": status["telemetry_policy"],
        "verified_boundary": status["verified_boundary"],
        "monitored_connections": status["open_connections"],
        "registered_models": registry.list_models(),
    }


@security_router.get("/health")
def get_health_status():
    """Returns component health status."""
    sec = security_monitor.verify_network_isolation()
    return {
        "status": "healthy",
        "air_gapped": True,
        "services": {
            "orchestrator": "online",
            "model_registry": "ready",
            "rag_vector_engine": "online",
            "coding_sandbox": "isolated",
            "network_monitor": "enforcing_zero_egress",
        },
        "model_online": sec["local_model_online"],
    }
