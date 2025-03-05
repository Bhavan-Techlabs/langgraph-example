# code_generator.py
import os
import json
from typing import Dict, Any, List
import shutil
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from database import get_project_path


class LangGraphCodeGenerator:
    """Generates LangGraph code based on workflow definitions"""

    def __init__(self):
        # Set up Jinja2 environment for code templates
        self.template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def generate_code(self, workflow: Dict[str, Any]) -> bool:
        """Generate LangGraph code for the given workflow"""
        workflow_id = workflow["id"]
        project_path = get_project_path(workflow_id)

        # Create project directory structure
        self._create_directory_structure(project_path)

        # Generate code files
        self._generate_init_files(project_path)
        self._generate_state_file(project_path, workflow)
        self._generate_tools_file(project_path, workflow)
        self._generate_nodes_file(project_path, workflow)
        self._generate_agent_file(project_path, workflow)
        self._generate_requirements_file(project_path)
        self._generate_langgraph_config(project_path, workflow)
        self._generate_env_file(project_path)

        return True

    def _create_directory_structure(self, project_path: str) -> None:
        """Create the directory structure for the LangGraph project"""
        # Create main directories
        os.makedirs(project_path, exist_ok=True)
        os.makedirs(os.path.join(project_path, "my_agent"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "my_agent", "utils"), exist_ok=True)

    def _generate_init_files(self, project_path: str) -> None:
        """Generate __init__.py files"""
        # Main package __init__.py
        with open(os.path.join(project_path, "my_agent", "__init__.py"), "w") as f:
            f.write("# Auto-generated package\n")

        # Utils package __init__.py
        with open(
            os.path.join(project_path, "my_agent", "utils", "__init__.py"), "w"
        ) as f:
            f.write("# Auto-generated utils package\n")

    def _generate_state_file(self, project_path: str, workflow: Dict[str, Any]) -> None:
        """Generate the state.py file"""
        template = self.env.get_template("state.py.j2")

        # Analyze workflow to determine state fields
        state_fields = self._analyze_state_fields(workflow)

        # Render template
        content = template.render(
            workflow_name=workflow["name"], state_fields=state_fields
        )

        # Write file
        with open(
            os.path.join(project_path, "my_agent", "utils", "state.py"), "w"
        ) as f:
            f.write(content)

    def _generate_tools_file(self, project_path: str, workflow: Dict[str, Any]) -> None:
        """Generate the tools.py file"""
        template = self.env.get_template("tools.py.j2")

        # Extract tools from workflow
        tools = self._extract_tools(workflow)

        # Render template
        content = template.render(workflow_name=workflow["name"], tools=tools)

        # Write file
        with open(
            os.path.join(project_path, "my_agent", "utils", "tools.py"), "w"
        ) as f:
            f.write(content)

    def _generate_nodes_file(self, project_path: str, workflow: Dict[str, Any]) -> None:
        """Generate the nodes.py file"""
        template = self.env.get_template("nodes.py.j2")

        # Extract nodes info
        nodes_info = self._analyze_nodes(workflow)

        # Render template
        content = template.render(workflow_name=workflow["name"], nodes=nodes_info)

        # Write file
        with open(
            os.path.join(project_path, "my_agent", "utils", "nodes.py"), "w"
        ) as f:
            f.write(content)

    def _generate_agent_file(self, project_path: str, workflow: Dict[str, Any]) -> None:
        """Generate the agent.py file with graph definition"""
        template = self.env.get_template("agent.py.j2")

        # Extract edges and build the graph structure
        edges = workflow["edges"]
        graph_structure = self._build_graph_structure(workflow)

        # Render template
        content = template.render(
            workflow_name=workflow["name"],
            workflow_id=workflow["id"],
            nodes=workflow["nodes"],
            edges=edges,
            graph_structure=graph_structure,
            has_llm_nodes=any(node["type"] == "llm" for node in workflow["nodes"]),
            has_tool_nodes=any(node["type"] == "tool" for node in workflow["nodes"]),
        )

        # Write file
        with open(os.path.join(project_path, "my_agent", "agent.py"), "w") as f:
            f.write(content)

    def _generate_requirements_file(self, project_path: str) -> None:
        """Generate the requirements.txt file"""
        requirements = [
            "langgraph>=0.0.25",
            "langchain>=0.1.0",
            "langchain-openai>=0.0.1",
            "python-dotenv>=1.0.0",
            "pydantic>=2.0.0",
        ]
