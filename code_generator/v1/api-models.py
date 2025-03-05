from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class WorkflowRequest(BaseModel):
    """Request model for creating or updating a workflow."""

    name: str = Field(..., description="Name of the workflow")
    description: Optional[str] = Field(None, description="Description of the workflow")
    definition: Dict[str, Any] = Field(
        ..., description="JSON definition of the workflow"
    )


class WorkflowResponse(BaseModel):
    """Response model for workflow operations."""

    id: str = Field(..., description="Unique identifier for the workflow")
    name: str = Field(..., description="Name of the workflow")
    status: str = Field(..., description="Status of the workflow")
    code_path: str = Field(..., description="Path to the generated code")


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""

    id: str = Field(..., description="Unique identifier for the workflow")
    name: str = Field(..., description="Name of the workflow")
    status: str = Field(..., description="Status of the workflow")
    code_path: str = Field(..., description="Path to the generated code")


class WorkflowExecutionRequest(BaseModel):
    """Request model for executing a workflow."""

    inputs: Dict[str, Any] = Field(
        ..., description="Input data for the workflow execution"
    )


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution."""

    workflow_id: str = Field(..., description="Workflow identifier")
    execution_id: str = Field(..., description="Execution identifier")
    status: str = Field(..., description="Status of the execution")


class NodeDefinition(BaseModel):
    """Model for a node in the workflow graph."""

    id: str = Field(..., description="Unique identifier for the node")
    type: str = Field(..., description="Type of the node")
    data: Dict[str, Any] = Field(..., description="Node configuration data")
    position: Dict[str, float] = Field(..., description="Position in the UI")


class EdgeDefinition(BaseModel):
    """Model for an edge in the workflow graph."""

    id: str = Field(..., description="Unique identifier for the edge")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    sourceHandle: Optional[str] = Field(None, description="Source handle ID")
    targetHandle: Optional[str] = Field(None, description="Target handle ID")


class GraphDefinition(BaseModel):
    """Model for the complete workflow graph."""

    nodes: List[NodeDefinition] = Field(..., description="List of nodes in the graph")
    edges: List[EdgeDefinition] = Field(..., description="List of edges in the graph")
