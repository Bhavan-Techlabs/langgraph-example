# human_intervention_manager.py
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from models import (
    HumanInterventionRequest,
    HumanInterventionResponse,
    NodeExecution,
    WorkflowExecution,
)
from execution_manager import ExecutionManager


class HumanInterventionManager:
    """Manages human-in-the-loop interactions"""

    def __init__(self, db: Session):
        self.db = db

    def create_intervention_request(
        self,
        node_execution_id: int,
        prompt: str,
        context_data: Dict[str, Any],
        options: Optional[Dict[str, str]] = None,
        priority: int = 1,
        expires_in_minutes: int = 60,
    ) -> int:
        """Create a new human intervention request"""
        # Get the node execution to ensure it exists
        node_execution = (
            self.db.query(NodeExecution)
            .filter(NodeExecution.id == node_execution_id)
            .first()
        )

        if not node_execution:
            raise ValueError(f"Node execution {node_execution_id} not found")

        # Create the request
        now = datetime.now()
        expires_at = now + timedelta(minutes=expires_in_minutes)

        request = HumanInterventionRequest(
            node_execution_id=node_execution_id,
            status="PENDING",
            created_at=now,
            expires_at=expires_at,
            request_data={
                "prompt": prompt,
                "context": context_data,
                "options": options,
            },
            request_type="APPROVAL",
            priority=priority,
        )

        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)

        # Update node execution status
        node_execution.status = "WAITING_FOR_HUMAN"
        self.db.commit()

        return request.id

    def get_pending_interventions(self) -> List[Dict[str, Any]]:
        """Get all pending intervention requests"""
        # Join with NodeExecution to get workflow and node information
        query = (
            self.db.query(HumanInterventionRequest, NodeExecution, WorkflowExecution)
            .join(
                NodeExecution,
                HumanInterventionRequest.node_execution_id == NodeExecution.id,
            )
            .join(
                WorkflowExecution,
                NodeExecution.workflow_execution_id == WorkflowExecution.id,
            )
            .filter(
                HumanInterventionRequest.status == "PENDING",
                HumanInterventionRequest.expires_at > datetime.now(),
            )
            .order_by(
                HumanInterventionRequest.priority.desc(),
                HumanInterventionRequest.created_at.asc(),
            )
        )

        results = []
        for req, node_exec, workflow_exec in query:
            results.append(
                {
                    "id": req.id,
                    "node_execution_id": req.node_execution_id,
                    "workflow_execution_id": node_exec.workflow_execution_id,
                    "workflow_id": workflow_exec.workflow_id,
                    "node_id": node_exec.node_id,
                    "node_name": self._get_node_name(node_exec.node_id),
                    "status": req.status,
                    "created_at": req.created_at,
                    "expires_at": req.expires_at,
                    "request_data": req.request_data,
                    "request_type": req.request_type,
                    "priority": req.priority,
                }
            )

        return results

    def get_intervention_request(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Get an intervention request by ID"""
        # Join with NodeExecution to get workflow and node information
        query = (
            self.db.query(HumanInterventionRequest, NodeExecution, WorkflowExecution)
            .join(
                NodeExecution,
                HumanInterventionRequest.node_execution_id == NodeExecution.id,
            )
            .join(
                WorkflowExecution,
                NodeExecution.workflow_execution_id == WorkflowExecution.id,
            )
            .filter(HumanInterventionRequest.id == request_id)
            .first()
        )

        if not query:
            return None

        req, node_exec, workflow_exec = query
        return {
            "id": req.id,
            "node_execution_id": req.node_execution_id,
            "workflow_execution_id": node_exec.workflow_execution_id,
            "workflow_id": workflow_exec.workflow_id,
            "node_id": node_exec.node_id,
            "node_name": self._get_node_name(node_exec.node_id),
            "status": req.status,
            "created_at": req.created_at,
            "expires_at": req.expires_at,
            "request_data": req.request_data,
            "request_type": req.request_type,
            "priority": req.priority,
        }

    def submit_response(
        self,
        request_id: int,
        user_id: int,
        response_data: Dict[str, Any],
        notes: Optional[str] = None,
    ) -> bool:
        """Submit a human response to an intervention request"""
        # Get the request to ensure it exists and is pending
        request = (
            self.db.query(HumanInterventionRequest)
            .filter(
                HumanInterventionRequest.id == request_id,
                HumanInterventionRequest.status == "PENDING",
            )
            .first()
        )

        if not request:
            return False

        # Create the response
        response = HumanInterventionResponse(
            request_id=request_id,
            user_id=user_id,
            created_at=datetime.now(),
            response_data=response_data,
            notes=notes,
        )

        self.db.add(response)

        # Update request status
        request.status = "ANSWERED"

        # Get the node execution to update its status
        node_execution = (
            self.db.query(NodeExecution)
            .filter(NodeExecution.id == request.node_execution_id)
            .first()
        )

        if node_execution:
            node_execution.status = "RESUMING"
            node_execution.output_data = {
                "human_response": response_data,
                "human_notes": notes,
            }

        self.db.commit()
        return True

    def resume_workflow_execution(self, request_id: int) -> bool:
        """Resume a workflow execution after human intervention"""
        # Get the request and associated execution info
        query = (
            self.db.query(HumanInterventionRequest, NodeExecution, WorkflowExecution)
            .join(
                NodeExecution,
                HumanInterventionRequest.node_execution_id == NodeExecution.id,
            )
            .join(
                WorkflowExecution,
                NodeExecution.workflow_execution_id == WorkflowExecution.id,
            )
            .filter(HumanInterventionRequest.id == request_id)
            .first()
        )

        if not query:
            return False

        req, node_exec, workflow_exec = query

        # Use the execution manager to resume the workflow
        execution_manager = ExecutionManager(self.db)
        execution_manager.resume_execution(workflow_exec.id, node_exec.id, req.id)

        return True

    def _get_node_name(self, node_id: int) -> str:
        """Helper to get node name from ID"""
        from models import Node

        node = self.db.query(Node).filter(Node.id == node_id).first()
        return node.name if node else f"Node-{node_id}"
