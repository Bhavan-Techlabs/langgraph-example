"""
This file will create the code for the langgraph agent based on the file structure given on
https://langchain-ai.github.io/langgraph/concepts/application_structure/
"""

import os
import json
from pathlib import Path
import shutil

class LangGraphProjectGenerator:
    def __init__(self, config_file: str):
        """Initialize the project generator with a configuration file."""
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        self.agent_name = self.config.get('agent_name', 'my_agent')
        self.root_dir = Path(self.agent_name + '-app')

    def create_directory_structure(self):
        """Create the basic directory structure for the project."""
        # Create main project directory
        self.root_dir.mkdir(exist_ok=True)
        
        # Create agent directory
        agent_dir = self.root_dir / self.agent_name
        agent_dir.mkdir(exist_ok=True)
        
        # Create utils directory
        utils_dir = agent_dir / 'utils'
        utils_dir.mkdir(exist_ok=True)
        
        # Create empty __init__.py files
        (agent_dir / '__init__.py').touch()
        (utils_dir / '__init__.py').touch()

    def generate_tools_file(self):
        """Generate the tools.py file with tool definitions."""
        tools_content = """from typing import Any, Dict
from langchain.tools import BaseTool

{tool_classes}

def get_tools() -> list[BaseTool]:
    \"\"\"Returns a list of tools available to the agent.\"\"\"
    return [{tool_instances}]
"""
        tool_classes = []
        tool_instances = []
        
        for tool in self.config.get('tools', []):
            tool_name = tool['name']
            tool_description = tool.get('description', '')
            
            tool_class = f"""
class {tool_name}Tool(BaseTool):
    name = "{tool_name.lower()}"
    description = "{tool_description}"
    
    def _run(self, input_data: str) -> str:
        # TODO: Implement tool logic
        pass
    
    async def _arun(self, input_data: str) -> str:
        # TODO: Implement async tool logic
        raise NotImplementedError("Async not implemented")
"""
            tool_classes.append(tool_class)
            tool_instances.append(f"{tool_name}Tool()")
        
        tools_content = tools_content.format(
            tool_classes="\n".join(tool_classes),
            tool_instances=", ".join(tool_instances)
        )
        
        with open(self.root_dir / self.agent_name / 'utils' / 'tools.py', 'w') as f:
            f.write(tools_content)

    def generate_state_file(self):
        """Generate the state.py file with state definitions."""
        state_content = """from typing import TypedDict, List, Optional
from langchain.schema import BaseMessage

class AgentState(TypedDict):
    messages: List[BaseMessage]
    current_step: str
    next_step: Optional[str]
    task_status: str
"""
        with open(self.root_dir / self.agent_name / 'utils' / 'state.py', 'w') as f:
            f.write(state_content)

    def generate_nodes_file(self):
        """Generate the nodes.py file with node functions."""
        nodes_content = """from typing import Annotated, Sequence, TypeVar
from langgraph.graph import StateGraph
from .state import AgentState

def process_task(state: AgentState) -> AgentState:
    \"\"\"Process the current task.\"\"\"
    # TODO: Implement task processing logic
    return state

def decide_next_step(state: AgentState) -> str:
    \"\"\"Decide the next step in the workflow.\"\"\"
    # TODO: Implement decision logic
    return "end"
"""
        with open(self.root_dir / self.agent_name / 'utils' / 'nodes.py', 'w') as f:
            f.write(nodes_content)

    def generate_agent_file(self):
        """Generate the main agent.py file."""
        agent_content = f"""from typing import Dict, Any
from langgraph.graph import StateGraph
from langchain.chat_models import ChatOpenAI
from .utils.state import AgentState
from .utils.tools import get_tools
from .utils.nodes import process_task, decide_next_step

class {self.agent_name.title()}Agent:
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.llm = ChatOpenAI(model_name=model_name)
        self.tools = get_tools()
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        \"\"\"Create the agent workflow graph.\"\"\"
        workflow = StateGraph(AgentState)
        
        # Add nodes to the graph
        workflow.add_node("process", process_task)
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "process",
            decide_next_step,
            {
                "continue": "process",
                "end": None
            }
        )
        
        workflow.set_entry_point("process")
        return workflow.compile()

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Run the agent workflow with the given input.\"\"\"
        initial_state = {
            "messages": [],
            "current_step": "start",
            "next_step": None,
            "task_status": "in_progress"
        }
        
        result = self.workflow.invoke(initial_state)
        return result
"""
        with open(self.root_dir / self.agent_name / 'agent.py', 'w') as f:
            f.write(agent_content)

    def generate_requirements_file(self):
        """Generate the requirements.txt file."""
        requirements = """langchain>=0.1.0
langgraph>=0.0.10
openai>=1.0.0
python-dotenv>=0.19.0
"""
        with open(self.root_dir / 'requirements.txt', 'w') as f:
            f.write(requirements)

    def generate_env_file(self):
        """Generate the .env file."""
        env_content = """# OpenAI API Key
OPENAI_API_KEY=your-api-key-here

# Other configuration variables
MODEL_NAME=gpt-3.5-turbo
"""
        with open(self.root_dir / '.env', 'w') as f:
            f.write(env_content)

    def generate_config_file(self):
        """Generate the langgraph.json file."""
        config_content = json.dumps(self.config, indent=2)
        with open(self.root_dir / 'langgraph.json', 'w') as f:
            f.write(config_content)

    def generate_project(self):
        """Generate the complete project structure."""
        self.create_directory_structure()
        self.generate_tools_file()
        self.generate_state_file()
        self.generate_nodes_file()
        self.generate_agent_file()
        self.generate_requirements_file()
        self.generate_env_file()
        self.generate_config_file()
        
        print(f"Project generated successfully at: {self.root_dir}")

if __name__ == "__main__":
    # Example usage
    example_config = {
        "agent_name": "my_agent",
        "tools": [
            {
                "name": "Calculator",
                "description": "Performs basic mathematical calculations"
            },
            {
                "name": "WebSearch",
                "description": "Searches the web for information"
            }
        ]
    }
    
    # Save example config to file
    with open('example_langgraph.json', 'w') as f:
        json.dump(example_config, indent=2, fp=f)
    
    # Generate project from config
    generator = LangGraphProjectGenerator('example_langgraph.json')
    generator.generate_project()