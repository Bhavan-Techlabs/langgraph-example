# app.py
import os
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
import models
from workflow_manager import WorkflowManager
from execution_manager import ExecutionManager
from code_generator import LangGraphCodeGenerator

app = FastAPI(title="Multi-Agent Orchestration Platform")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for API requests/responses
class NodeConfigModel(BaseModel):
    type: str
    name: str
    config: Dict[str, Any]
    position: Dict[str, float]

class EdgeModel(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str]
    targetHandle: Optional[str]
    label: Optional[str]

class WorkflowModel(BaseModel):
    name: str
    description: Optional[str] = None
    nodes: List[NodeConfigModel]
    edges: List[EdgeModel]
    metadata: Optional[Dict[str, Any]] = {}

class ExecutionRequestModel(BaseModel):
    workflow_id: int
    input_data: Dict[str, Any]

class ExecutionResponseModel(BaseModel):
    execution_id: int
    status: str
    output: Optional[Dict[str, Any]] = None

# Routes
@app.post("/api/workflows", status_code=201)
def create_workflow(
    workflow: WorkflowModel, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new workflow and generate LangGraph code"""
    workflow_manager = WorkflowManager(db)
    workflow_id = workflow_manager.create_workflow(workflow)
    
    # Generate code in background
    background_tasks.add_task(
        generate_langgraph_code,
        workflow_id=workflow_id,
        db=db
    )
    
    return {"workflow_id": workflow_id, "message": "Workflow created successfully"}

@app.get("/api/workflows")
def get_workflows(db: Session = Depends(get_db)):
    """Get all workflows"""
    workflow_manager = WorkflowManager(db)
    return workflow_manager.get_all_workflows()

@app.get("/api/workflows/{workflow_id}")
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Get a specific workflow"""
    workflow_manager = WorkflowManager(db)
    workflow = workflow_manager.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@app.put("/api/workflows/{workflow_id}")
def update_workflow(
    workflow_id: int,
    workflow: WorkflowModel,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update an existing workflow and regenerate LangGraph code"""
    workflow_manager = WorkflowManager(db)
    success = workflow_manager.update_workflow(workflow_id, workflow)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Regenerate code in background
    background_tasks.add_task(
        generate_langgraph_code,
        workflow_id=workflow_id,
        db=db
    )
    
    return {"message": "Workflow updated successfully"}

@app.delete("/api/workflows/{workflow_id}")
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Delete a workflow"""
    workflow_manager = WorkflowManager(db)
    success = workflow_manager.delete_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"message": "Workflow deleted successfully"}

@app.post("/api/workflows/{workflow_id}/execute", response_model=ExecutionResponseModel)
def execute_workflow(
    workflow_id: int,
    execution_request: ExecutionRequestModel,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Execute a workflow with the provided input data"""
    execution_manager = ExecutionManager(db)
    execution_id = execution_manager.start_execution(
        workflow_id, 
        execution_request.input_data
    )
    
    # Run execution in background
    background_tasks.add_task(
        run_workflow_execution,
        execution_id=execution_id,
        db=db
    )
    
    return {
        "execution_id": execution_id,
        "status": "RUNNING",
        "output": None
    }

@app.get("/api/executions/{execution_id}", response_model=ExecutionResponseModel)
def get_execution_status(execution_id: int, db: Session = Depends(get_db)):
    """Get the status of a workflow execution"""
    execution_manager = ExecutionManager(db)
    execution = execution_manager.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return {
        "execution_id": execution_id,
        "status": execution.status,
        "output": execution.output_data
    }

# Background tasks
def generate_langgraph_code(workflow_id: int, db: Session):
    """Generate LangGraph code for a workflow"""
    workflow_manager = WorkflowManager(db)
    workflow = workflow_manager.get_workflow(workflow_id)
    if not workflow:
        return
    
    code_generator = LangGraphCodeGenerator()
    code_generator.generate_code(workflow)

def run_workflow_execution(execution_id: int, db: Session):
    """Run a workflow execution"""
    execution_manager = ExecutionManager(db)
    execution_manager.run_execution(execution_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
