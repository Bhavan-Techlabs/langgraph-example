import os
import logging
import shutil
from typing import Dict, Any, List, Optional
import importlib.util
import sys


class LangGraphCodeGenerator:
    """
    Generator to create LangGraph agent code from parsed workflow definitions.
    """

    def __init__(self, output_path: str):
        """
        Initialize the code generator.

        Args:
            output_path: Path where generated code will be stored
        """
        self.output_path = output_path
        self.logger = logging.getLogger(__name__)
        os.makedirs(output_path, exist_ok=True)

    def generate(
        self, workflow_id: str, parsed_workflow: Dict[str, Any], update: bool = False
    ) -> str:
        """
        Generate LangGraph code from a parsed workflow.

        Args:
            workflow_id: Unique identifier for the workflow
            parsed_workflow: Parsed workflow structure
            update: Whether this is an update to an existing workflow

        Returns:
            Path to the generated code
        """
        self.logger.info(f"Generating LangGraph code for workflow {workflow_id}")

        # Create workflow directory
        workflow_dir = os.path.join(self.output_path, workflow_id)
        module_name = f"workflow_{workflow_id.replace('-', '_')}"

        # If updating, clean up existing code
        if update and os.path.exists(workflow_dir):
            # Clean up but keep any non-generated files
            self._clean_generated_files(workflow_dir)
        else:
            # Create new directory
            os.makedirs(workflow_dir, exist_ok=True)
            os.makedirs(os.path.join(workflow_dir, "utils"), exist_ok=True)

        # Generate files
        self._generate_init_file(workflow_dir)
        self._generate_utils_init_file(os.path.join(workflow_dir, "utils"))
        self._generate_state_file(workflow_dir, parsed_workflow)
        self._generate_tools_file(workflow_dir, parsed_workflow)
        self._generate_nodes_file(workflow_dir, parsed_workflow)
        self._generate_agent_file(workflow_dir, parsed_workflow, module_name)
        self._generate_config_file(workflow_dir, parsed_workflow)

        self.logger.info(
            f"LangGraph code generation completed for workflow {workflow_id}"
        )
        return workflow_dir

    def cleanup(self, workflow_id: str) -> None:
        """
        Clean up generated code for a workflow.

        Args:
            workflow_id: ID of the workflow to clean up
        """
        workflow_dir = os.path.join(self.output_path, workflow_id)
        if os.path.exists(workflow_dir):
            self.logger.info(f"Removing generated code for workflow {workflow_id}")
            shutil.rmtree(workflow_dir)

    def _clean_generated_files(self, workflow_dir: str) -> None:
        """
        Clean up generated files in a workflow directory but preserve any custom files.

        Args:
            workflow_dir: Path to the workflow directory
        """
        # List of files we generate and should clean up
        generated_files = [
            "__init__.py",
            "agent.py",
            "langgraph.json",
        ]

        # List of directories we generate and should clean up
        generated_dirs = [
            "utils",
        ]

        for file in generated_files:
            file_path = os.path.join(workflow_dir, file)
            if os.path.exists(file_path):
                os.remove(file_path)

        for dir_name in generated_dirs:
            dir_path = os.path.join(workflow_dir, dir_name)
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                os.makedirs(dir_path, exist_ok=True)

    def _generate_init_file(self, workflow_dir: str) -> None:
        """Generate the __init__.py file for the workflow package."""
        init_path = os.path.join(workflow_dir, "__init__.py")
        with open(init_path, "w") as f:
            f.write('"""Auto-generated LangGraph agent application."""\n\n')
            f.write("from .agent import create_agent, run_agent\n")

    def _generate_utils_init_file(self, utils_dir: str) -> None:
        """Generate the __init__.py file for the utils package."""
        init_path = os.path.join(utils_dir, "__init__.py")
        with open(init_path, "w") as f:
            f.write('"""Auto-generated utility modules for LangGraph agents."""\n\n')
            f.write("from .state import State\n")
            f.write("from .tools import register_tools\n")
            f.write("from .nodes import register_nodes\n")

    def _generate_state_file(
        self, workflow_dir: str, parsed_workflow: Dict[str, Any]
    ) -> None:
        """Generate the state.py file defining the LangGraph state class."""
        state_path = os.path.join(workflow_dir, "utils", "state.py")

        # Extract state variables from the workflow
        state_vars = parsed_workflow.get("state", {})

        with open(state_path, "w") as f:
            f.write('"""Auto-generated state definition for LangGraph agent."""\n\n')
            f.write("from typing import Dict, Any, List, Optional\n")
            f.write("from pydantic import BaseModel, Field\n\n")

            f.write("class State(BaseModel):\n")
            f.write('    """State definition for the LangGraph workflow."""\n\n')

            # Add state variables with their types
            if not state_vars:
                f.write("    # Default state variables\n")
                f.write(
                    "    messages: List[Dict[str, Any]] = Field(default_factory=list)\n"
                )
                f.write("    current_node: Optional[str] = None\n")
                f.write('    workflow_status: str = "running"\n')
            else:
                for var_name, var_config in state_vars.items():
                    var_type = var_config.get("type", "Any")
                    default = var_config.get("default", None)

                    if default is None:
                        if var_type == "List":
                            f.write(
                                f"    {var_name}: {var_type}[Any] = Field(default_factory=list)\n"
                            )
                        elif var_type == "Dict":
                            f.write(
                                f"    {var_name}: {var_type}[str, Any] = Field(default_factory=dict)\n"
                            )
                        else:
                            f.write(f"    {var_name}: Optional[{var_type}] = None\n")
                    else:
                        f.write(f"    {var_name}: {var_type} = {repr(default)}\n")

                # Always include these core state variables
                f.write("\n    # Core state tracking variables\n")
                f.write(
                    "    messages: List[Dict[str, Any]] = Field(default_factory=list)\n"
                )
                f.write("    current_node: Optional[str] = None\n")
                f.write('    workflow_status: str = "running"\n')
