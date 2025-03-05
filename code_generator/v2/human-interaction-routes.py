# human_interaction_routes.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from database import get_db
from models import HumanInterventionRequest, HumanInterventionResponse
from human_intervention_manager import HumanInterventionManager

router = APIRouter(prefix="/api/human-interventions", tags=["Human-in-the-Loop"])


# Models for API requests/responses
class InterventionRequestModel(BaseModel):
    node_execution_id: int
    prompt: str
    context_data: Dict[str, Any]
    options: Optional[Dict[str, str]] = None
    priority: int = 1
    expires_in_minutes: int = 60


class InterventionResponseModel(BaseModel):
    request_id: int
    response_data: Dict[str, Any]
    notes: Optional[str] = None


class PendingInterventionModel(BaseModel):
    id: int
    node_execution_id: int
    workflow_execution_id: int
    workflow_id: int
    node_id: int
    node_name: str
    status: str
    created_at: datetime
    expires_at: datetime
    request_data: Dict[str, Any]
    request_type: str
    priority: int


# Routes
@router.get("/pending", response_model=List[PendingInterventionModel])
def get_pending_interventions(db: Session = Depends(get_db)):
    """Get all pending human intervention requests"""
    manager = HumanInterventionManager(db)
    return manager.get_pending_interventions()


@router.get("/{request_id}", response_model=PendingInterventionModel)
def get_intervention_request(request_id: int, db: Session = Depends(get_db)):
    """Get a specific intervention request"""
    manager = HumanInterventionManager(db)
    request = manager.get_intervention_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Intervention request not found")
    return request


@router.post("/{request_id}/respond", status_code=200)
def respond_to_intervention(
    request_id: int,
    response: InterventionResponseModel,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    """Submit a human response to an intervention request"""
    manager = HumanInterventionManager(db)
    success = manager.submit_response(
        request_id=request_id,
        user_id=1,  # Replace with actual user authentication
        response_data=response.response_data,
        notes=response.notes,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Failed to submit response")

    # Resume workflow execution in background
    if background_tasks:
        background_tasks.add_task(
            manager.resume_workflow_execution, request_id=request_id
        )

    return {"message": "Response submitted successfully"}


@router.post("/create", status_code=201)
def create_intervention_request(
    request: InterventionRequestModel, db: Session = Depends(get_db)
):
    """Create a new human intervention request (usually called by the workflow engine)"""
    manager = HumanInterventionManager(db)
    request_id = manager.create_intervention_request(
        node_execution_id=request.node_execution_id,
        prompt=request.prompt,
        context_data=request.context_data,
        options=request.options,
        priority=request.priority,
        expires_in_minutes=request.expires_in_minutes,
    )

    return {"request_id": request_id, "message": "Intervention request created"}
