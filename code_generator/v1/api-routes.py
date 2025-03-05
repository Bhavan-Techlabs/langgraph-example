from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
import logging
from uuid import uuid4
import os
import json
from typing import Dict, Any, Optional

from app.api.models import (
    WorkflowRequest,
    WorkflowResponse,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowStatusResponse,
)
from app.core.parser import WorkflowParser
from app.core.generator import LangGraphCodeGenerator
from app.core.executor import LangGraphExecutor
from app.core.state_manager import AgentStateManager
from app.core.config import settings

# Create router
router = APIRouter()

# In-memory store for workflow statuses
workflow_statuses: Dict[str, Dict[str, Any]] = {}


# Get dependencies
def get_parser():
    return WorkflowParser()


def get_generator():
    return LangGraphCodeGenerator(settings.GENERATED_CODE_PATH)


def get_executor():
    return LangGraphExecutor()


def get_state_manager():
    return AgentStateManager()


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    workflow: WorkflowRequest,
    parser: WorkflowParser = Depends(get_parser),
    generator: LangGraphCodeGenerator = Depends(get_generator),
):
    """Create a new workflow from the provided JSON definition."""
    try:
        # Generate a unique workflow ID
        workflow_id = str(uuid4())

        # Parse the workflow
        parsed_workflow = parser.parse(workflow.definition)

        # Generate LangGraph code
        code_path = generator.generate(workflow_id, parsed_workflow)

        # Store workflow status
        workflow_statuses[workflow_id] = {
            "id": workflow_id,
            "name": workflow.name,
            "status": "created",
            "code_path": code_path,
        }

        return WorkflowResponse(
            id=workflow_id, name=workflow.name, status="created", code_path=code_path
        )
    except Exception as e:
        logging.error(f"Error creating workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}",
        )


@router.get("/workflows/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """Get the status of a specific workflow."""
    if workflow_id not in workflow_statuses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID {workflow_id} not found",
        )

    return WorkflowStatusResponse(**workflow_statuses[workflow_id])


@router.post(
    "/workflows/{workflow_id}/execute", response_model=WorkflowExecutionResponse
)
async def execute_workflow(
    workflow_id: str,
    execution_request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks,
    executor: LangGraphExecutor = Depends(get_executor),
    state_manager: AgentStateManager = Depends(get_state_manager),
):
    """Execute a workflow with the given inputs."""
    if workflow_id not in workflow_statuses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID {workflow_id} not found",
        )

    # Update workflow status
    workflow_statuses[workflow_id]["status"] = "running"

    # Create execution ID
    execution_id = str(uuid4())

    # Execute workflow in background
    background_tasks.add_task(
        _execute_workflow_task,
        workflow_id,
        execution_id,
        execution_request.inputs,
        workflow_statuses[workflow_id]["code_path"],
        executor,
        state_manager,
    )

    return WorkflowExecutionResponse(
        workflow_id=workflow_id, execution_id=execution_id, status="running"
    )


@router.get(
    "/workflows/{workflow_id}/executions/{execution_id}", response_model=Dict[str, Any]
)
async def get_execution_result(
    workflow_id: str,
    execution_id: str,
    state_manager: AgentStateManager = Depends(get_state_manager),
):
    """Get the result of a workflow execution."""
    # Check if the execution exists and get its state
    execution_state = state_manager.get_execution_state(workflow_id, execution_id)
    if not execution_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} for workflow {workflow_id} not found",
        )

    return execution_state


@router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow: WorkflowRequest,
    parser: WorkflowParser = Depends(get_parser),
    generator: LangGraphCodeGenerator = Depends(get_generator),
):
    """Update an existing workflow."""
    if workflow_id not in workflow_statuses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID {workflow_id} not found",
        )

    try:
        # Parse the updated workflow
        parsed_workflow = parser.parse(workflow.definition)

        # Generate updated LangGraph code
        code_path = generator.generate(workflow_id, parsed_workflow, update=True)

        # Update workflow status
        workflow_statuses[workflow_id].update(
            {"name": workflow.name, "status": "updated", "code_path": code_path}
        )

        return WorkflowResponse(
            id=workflow_id, name=workflow.name, status="updated", code_path=code_path
        )
    except Exception as e:
        logging.error(f"Error updating workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workflow: {str(e)}",
        )


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str, generator: LangGraphCodeGenerator = Depends(get_generator)
):
    """Delete a workflow."""
    if workflow_id not in workflow_statuses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID {workflow_id} not found",
        )

    try:
        # Remove generated code
        generator.cleanup(workflow_id)

        # Remove from status tracking
        del workflow_statuses[workflow_id]

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content={})
    except Exception as e:
        logging.error(f"Error deleting workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workflow: {str(e)}",
        )


async def _execute_workflow_task(
    workflow_id: str,
    execution_id: str,
    inputs: Dict[str, Any],
    code_path: str,
    executor: LangGraphExecutor,
    state_manager: AgentStateManager,
):
    """Background task to execute a workflow."""
    try:
        # Initialize state
        state_manager.initialize_execution(workflow_id, execution_id, inputs)

        # Execute the workflow
        result = executor.execute(
            code_path, inputs, workflow_id, execution_id, state_manager
        )

        # Update workflow status
        workflow_statuses[workflow_id]["status"] = "completed"

        # Update execution state
        state_manager.update_execution_state(
            workflow_id, execution_id, {"status": "completed", "result": result}
        )
    except Exception as e:
        logging.error(f"Error executing workflow: {str(e)}", exc_info=True)

        # Update workflow status
        workflow_statuses[workflow_id]["status"] = "failed"

        # Update execution state
        state_manager.update_execution_state(
            workflow_id, execution_id, {"status": "failed", "error": str(e)}
        )
