# execution_manager.py
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json
import os
import importlib.util
import sys
import traceback

from models import WorkflowExecution, NodeExecution
from database import get_project_path


class ExecutionManager:
    """Manages the execution of workflows and tracks their progress"""

    def __init__(self, db: Session):
        self.db = db

    def start_execution(self, workflow_id: int, input_data: Dict[str, Any]) -> int:
        """Start a new workflow execution and return the execution ID"""
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status="CREATED",
            started_at=datetime.now(),
            input_data=input_data,
            metadata={},
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution.id

    def get_execution(self, execution_id: int) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID"""
        return (
            self.db.query(WorkflowExecution)
            .filter(WorkflowExecution.id == execution_id)
            .first()
        )

    def run_execution(self, execution_id: int) -> None:
        """Run a workflow execution"""
        execution = self.get_execution(execution_id)
        if not execution:
            return

        # Update status to running
        execution.status = "RUNNING"
        self.db.commit()

        try:
            # Dynamically import and run the generated agent code
            project_path = get_project_path(execution.workflow_id)
            agent_module_path = os.path.join(project_path, "my_agent", "agent.py")

            # Load the agent module
            spec = importlib.util.spec_from_file_location(
                "dynamic_agent", agent_module_path
            )
            agent_module = importlib.util.module_from_spec(spec)
            sys.modules["dynamic_agent"] = agent_module
            spec.loader.exec_module(agent_module)

            # Run the agent with input data
            try:
                # Get the graph from the module
                graph = agent_module.get_graph()

                # Set up execution tracking callbacks
                def node_callback(event):
                    """Callback for node execution events"""
                    if event["type"] == "node:start":
                        node_exec = NodeExecution(
                            workflow_execution_id=execution_id,
                            node_id=self._get_node_id_by_name(
                                event["node_name"], execution.workflow_id
                            ),
                            status="RUNNING",
                            started_at=datetime.now(),
                            input_data=event.get("inputs", {}),
                        )
                        self.db.add(node_exec)
                        self.db.commit()
                    elif event["type"] == "node:end":
                        node_exec = (
                            self.db.query(NodeExecution)
                            .filter(
                                NodeExecution.workflow_execution_id == execution_id,
                                NodeExecution.node_id
                                == self._get_node_id_by_name(
                                    event["node_name"], execution.workflow_id
                                ),
                                NodeExecution.status == "RUNNING",
                            )
                            .first()
                        )

                        if node_exec:
                            node_exec.status = "COMPLETED"
                            node_exec.finished_at = datetime.now()
                            node_exec.output_data = event.get("outputs", {})
                            self.db.commit()

                # Register callback
                graph.add_listener(node_callback)

                # Execute the graph
                result = graph.invoke(execution.input_data)

                # Update execution status
                execution.status = "COMPLETED"
                execution.finished_at = datetime.now()
                execution.output_data = result
                self.db.commit()

            except Exception as e:
                # Handle agent execution errors
                execution.status = "FAILED"
                execution.finished_at = datetime.now()
                execution.output_data = {
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
                self.db.commit()

                # Also update any running node executions
                running_nodes = (
                    self.db.query(NodeExecution)
                    .filter(
                        NodeExecution.workflow_execution_id == execution_id,
                        NodeExecution.status == "RUNNING",
                    )
                    .all()
                )

                for node in running_nodes:
                    node.status = "FAILED"
                    node.finished_at = datetime.now()
                    node.error = str(e)

                self.db.commit()

        except Exception as e:
            # Handle system-level errors
            execution.status = "ERROR"
            execution.finished_at = datetime.now()
            execution.output_data = {
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
            self.db.commit()

    def _get_node_id_by_name(self, node_name: str, workflow_id: int) -> int:
        """Helper to get node database ID from node name"""
        from models import Node

        node = (
            self.db.query(Node)
            .filter(Node.workflow_id == workflow_id, Node.name == node_name)
            .first()
        )

        return node.id if node else 0
