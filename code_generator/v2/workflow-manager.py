# workflow_manager.py
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
import os
from datetime import datetime

from models import Workflow, Node, Edge, NodeConfig
from database import get_project_path


class WorkflowManager:
    """Manages workflow operations including CRUD and conversion"""

    def __init__(self, db: Session):
        self.db = db

    def create_workflow(self, workflow_data) -> int:
        """Create a new workflow from the provided data"""
        # Create workflow record
        workflow = Workflow(
            name=workflow_data.name,
            description=workflow_data.description,
            metadata=workflow_data.metadata,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=1,
            project_id=1,  # Default project for now, should be parameterized
        )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)

        # Add nodes
        for node_data in workflow_data.nodes:
            node = Node(
                workflow_id=workflow.id,
                node_id=node_data.name,  # Use name as node_id for now
                name=node_data.name,
                node_type_id=self._get_node_type_id(node_data.type),
                position=node_data.position,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.db.add(node)
            self.db.commit()
            self.db.refresh(node)

            # Add node configurations
            for key, value in node_data.config.items():
                node_config = NodeConfig(node_id=node.id, key=key, value=value)
                self.db.add(node_config)

        # Add edges
        for edge_data in workflow_data.edges:
            edge = Edge(
                workflow_id=workflow.id,
                edge_id=edge_data.id,
                source_node_id=edge_data.source,
                target_node_id=edge_data.target,
                source_handle=edge_data.sourceHandle,
                target_handle=edge_data.targetHandle,
                label=edge_data.label,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.db.add(edge)

        self.db.commit()
        return workflow.id

    def get_workflow(self, workflow_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a workflow by ID with its nodes and edges"""
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            return None

        nodes = self.db.query(Node).filter(Node.workflow_id == workflow_id).all()
        edges = self.db.query(Edge).filter(Edge.workflow_id == workflow_id).all()

        # Convert to API response format
        nodes_data = []
        for node in nodes:
            # Get node configs
            configs = (
                self.db.query(NodeConfig).filter(NodeConfig.node_id == node.id).all()
            )
            config_dict = {config.key: config.value for config in configs}

            nodes_data.append(
                {
                    "id": node.node_id,
                    "type": self._get_node_type_name(node.node_type_id),
                    "name": node.name,
                    "position": node.position,
                    "config": config_dict,
                }
            )

        edges_data = []
        for edge in edges:
            edges_data.append(
                {
                    "id": edge.edge_id,
                    "source": edge.source_node_id,
                    "target": edge.target_node_id,
                    "sourceHandle": edge.source_handle,
                    "targetHandle": edge.target_handle,
                    "label": edge.label,
                }
            )

        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "metadata": workflow.metadata,
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat(),
            "version": workflow.version,
            "nodes": nodes_data,
            "edges": edges_data,
        }

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows with basic info (no nodes/edges)"""
        workflows = self.db.query(Workflow).order_by(desc(Workflow.updated_at)).all()
        return [
            {
                "id": wf.id,
                "name": wf.name,
                "description": wf.description,
                "version": wf.version,
                "created_at": wf.created_at.isoformat(),
                "updated_at": wf.updated_at.isoformat(),
            }
            for wf in workflows
        ]

    def update_workflow(self, workflow_id: int, workflow_data) -> bool:
        """Update an existing workflow"""
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            return False

        # Update workflow properties
        workflow.name = workflow_data.name
        workflow.description = workflow_data.description
        workflow.metadata = workflow_data.metadata
        workflow.updated_at = datetime.now()
        workflow.version += 1

        # Delete existing nodes and edges (cascade will delete configs)
        self.db.query(Node).filter(Node.workflow_id == workflow_id).delete()
        self.db.query(Edge).filter(Edge.workflow_id == workflow_id).delete()
        self.db.commit()

        # Add new nodes
        for node_data in workflow_data.nodes:
            node = Node(
                workflow_id=workflow.id,
                node_id=node_data.name,
                name=node_data.name,
                node_type_id=self._get_node_type_id(node_data.type),
                position=node_data.position,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.db.add(node)
            self.db.commit()
            self.db.refresh(node)

            # Add node configurations
            for key, value in node_data.config.items():
                node_config = NodeConfig(node_id=node.id, key=key, value=value)
                self.db.add(node_config)

        # Add edges
        for edge_data in workflow_data.edges:
            edge = Edge(
                workflow_id=workflow.id,
                edge_id=edge_data.id,
                source_node_id=edge_data.source,
                target_node_id=edge_data.target,
                source_handle=edge_data.sourceHandle,
                target_handle=edge_data.targetHandle,
                label=edge_data.label,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.db.add(edge)

        self.db.commit()
        return True

    def delete_workflow(self, workflow_id: int) -> bool:
        """Delete a workflow and all associated data"""
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            return False

        # Delete will cascade to nodes and edges
        self.db.delete(workflow)
        self.db.commit()

        # Also clean up generated code files
        project_path = get_project_path(workflow_id)
        if os.path.exists(project_path):
            import shutil

            shutil.rmtree(project_path)

        return True

    def _get_node_type_id(self, type_name: str) -> int:
        """Get or create a node type ID based on the type name"""
        # This is a simplified version - in production, you'd query the NodeTypes table
        # For now, use a simple mapping for demo purposes
        node_type_map = {"llm": 1, "tool": 2, "memory": 3, "input": 4, "output": 5}
        return node_type_map.get(type_name.lower(), 99)  # Default to "other" type

    def _get_node_type_name(self, type_id: int) -> str:
        """Get the node type name from the type ID"""
        node_type_map = {
            1: "llm",
            2: "tool",
            3: "memory",
            4: "input",
            5: "output",
            99: "other",
        }
        return node_type_map.get(type_id, "unknown")
