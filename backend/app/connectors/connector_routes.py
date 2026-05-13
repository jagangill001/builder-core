from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.connectors.registry import connector_statuses, get_connector_status

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.get("")
def list_connectors() -> dict[str, object]:
    return {"items": connector_statuses()}


@router.get("/{name}/status")
def connector_status(name: str) -> dict[str, object]:
    status = get_connector_status(name)
    if status is None:
        raise HTTPException(status_code=404, detail={"code": "connector_not_found", "message": "Connector not found."})
    return status
