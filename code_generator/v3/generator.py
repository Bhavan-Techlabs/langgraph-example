import json
import os
from pathlib import Path
import re


def sanitize_name(name):
    """Convert a name to a valid Python identifier."""
    # Replace non-alphanumeric characters with underscores
    return re.sub(r"\W+", "_", name).lower()


def generate_workflow_config(workflow_data):
    """Generate a comprehensive workflow configuration."""
    return {
        "workflow_id": workflow_data.get("workflow_metadata", {}).get(
            "workflow_id", "default_workflow"
        ),
        "name": workflow_data.get("workflow_metadata", {}).get("name", "AI Workflow"),
        "description": workflow_data.get("workflow_metadata", {}).get(
            "description", ""
        ),
        "nodes": workflow_data.get("nodes", []),
        "edges": workflow_data.get("edges", []),
    }


def generate_state_file(workflow_config):
    """Generate a state management file for the workflow."""
    state_code = f"""from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage

class WorkflowState(BaseModel):
    \"\"\"State for the {workflow_config['name']} workflow.\"\"\"
    messages: List[BaseMessage] = Field(default_factory=list)
    current_node: Optional[str] = None
    workflow_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Add custom fields based on workflow configuration
    node_results: Dict[str, Any] = Field(default_factory=dict)
"""
    return state_code


def generate_nodes_file(workflow_config):
    """Generate nodes file with dynamic node creation."""
    nodes_code = f"""from typing import Dict, Any, Tuple, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from .state import WorkflowState

# Initialize the language model
model = ChatOpenAI(model="gpt-4")

"""

    # Generate node functions for each component
    for node in workflow_config["nodes"]:
        node_id = sanitize_name(node["id"])
        node_label = node.get("label", node["id"])

        nodes_code += f"""def {node_id}_node(state: WorkflowState, input: str) -> WorkflowState:
    \"\"\"Process node for {node_label}.\"\"\"
    # Node-specific configuration
    node_config = {node.get('config', {})}
    
    # Extract prompt template
    prompt_template = node_config.get('promptTemplate', {{}})
    prompt_content = prompt_template.get('content', 'Process the input.')
    
    # Prepare prompt
    full_prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_content),
        ("human", "{{input}}")
    ])
    
    # Invoke LLM
    chain = full_prompt | model
    response = chain.invoke({{"input": input}})
    
    # Update state
    state.messages.append(HumanMessage(content=input))
    state.messages.append(AIMessage(content=response.content))
    state.current_node = "{node_id}"
    state.node_results["{node_id}"] = {{
        "response": response.content,
        "config": node_config
    }}
    
    return state

"""

    # Generate routing logic
    nodes_code += """def route_next_node(state: WorkflowState, workflow_edges):
    \"\"\"Determine the next node based on workflow edges.\"\"\"
    current_node = state.current_node
    
    # Find matching edges
    next_edges = [edge for edge in workflow_edges if edge['source'] == current_node]
    
    if not next_edges:
        return None  # Workflow ends
    
    # For now, take the first edge (can be expanded for more complex routing)
    return next_edges[0]['target']
"""

    return nodes_code


def generate_workflow_file(workflow_config):
    """Generate the main workflow assembly file."""
    workflow_id = sanitize_name(workflow_config["workflow_id"])

    workflow_code = f"""from typing import Dict, Any
from langgraph.graph import StateGraph, END
from .state import WorkflowState
from .nodes import (
    {', '.join([sanitize_name(node['id']) + '_node' for node in workflow_config['nodes']])}
    route_next_node
)

def create_{workflow_id}_workflow():
    \"\"\"Create the workflow graph for {workflow_config['name']}.\"\"\"
    # Initialize the graph
    graph = StateGraph(WorkflowState)
    
    # Add nodes
    {';'.join([f"graph.add_node('{sanitize_name(node['id'])}', {sanitize_name(node['id'])}_node)" for node in workflow_config['nodes']])}
    
    # Define workflow routing
    workflow_edges = {workflow_config['edges']}
    
    def router(state: WorkflowState):
        next_node = route_next_node(state, workflow_edges)
        return next_node if next_node else END
    
    # Connect nodes
    graph.add_conditional_edges("supervisor", router)
    
    return graph.compile()

def run_workflow(input_text: str, initial_state: Dict[str, Any] = None):
    \"\"\"Run the workflow with given input.\"\"\"
    workflow = create_{workflow_id}_workflow()
    
    # Initialize state if not provided
    if initial_state is None:
        initial_state = WorkflowState().dict()
    
    # Invoke workflow
    result = workflow.invoke(initial_state | {{"input": input_text}})
    
    return result
"""
    return workflow_code


def generate_requirements_file():
    """Generate requirements file."""
    return """langchain>=0.1.0
langgraph>=0.0.15
langchain-openai>=0.0.5
pydantic>=2.0.0
python-dotenv>=1.0.0
"""


def create_workflow_project(workflow_data, output_dir="./generated_workflow"):
    """Create the workflow project structure."""
    # Parse and sanitize workflow configuration
    workflow_config = generate_workflow_config(workflow_data)
    workflow_id = sanitize_name(workflow_config["workflow_id"])

    # Create project structure
    base_dir = Path(output_dir)
    base_dir.mkdir(exist_ok=True, parents=True)

    workflow_dir = base_dir / workflow_id
    workflow_dir.mkdir(exist_ok=True)

    # Create package files
    (workflow_dir / "__init__.py").touch()

    # Generate and write files
    (workflow_dir / "state.py").write_text(generate_state_file(workflow_config))
    (workflow_dir / "nodes.py").write_text(generate_nodes_file(workflow_config))
    (workflow_dir / "workflow.py").write_text(generate_workflow_file(workflow_config))

    # Create requirements and environment files
    (base_dir / "requirements.txt").write_text(generate_requirements_file())

    print(f"Generated workflow project for '{workflow_config['name']}' in {output_dir}")
    return workflow_id


def generate_workflow_project(config_file=None, output_dir="./generated_workflow"):
    """
    Generate a LangGraph workflow project from a JSON configuration.

    Args:
        config_file (str, optional): Path to the workflow config JSON file
        output_dir (str, optional): Output directory for the project

    Returns:
        str: The name of the generated workflow project
    """
    # Load config
    if config_file:
        with open(config_file, "r") as f:
            workflow_data = json.load(f)
    else:
        # Use the provided workflow data as default
        workflow_data = json.loads(
            """
{
  "workflow_metadata": {
    "workflow_id": "wf_001",
    "name": "AI Workflow with Router Logic",
    "description": "A workflow where a supervisor agent routes tasks among specialized agents."
  },
  "nodes": [],
  "edges": []
}
"""
        )

    # Create the project
    workflow_name = create_workflow_project(workflow_data, output_dir)
    return workflow_name
