"""
This file will create the code for the langgraph agent based on the file structure given on
https://langchain-ai.github.io/langgraph/concepts/application_structure/
"""

import os
import json
import argparse
from pathlib import Path


def generate_init_file():
    return "# This file makes the directory a Python package\n"


def generate_tools_file(tools):
    tools_code = """from typing import List, Dict, Any, Optional
from langchain.tools import BaseTool

"""
    for tool in tools:
        tool_name = tool.get("name", "GenericTool")
        tool_description = tool.get("description", "A generic tool")
        tool_args = tool.get("args", [])

        args_str = ""
        for arg in tool_args:
            arg_name = arg.get("name", "arg")
            arg_type = arg.get("type", "str")
            arg_description = arg.get("description", "An argument")
            args_str += f'        "{arg_name}": {{"type": "{arg_type}", "description": "{arg_description}"}},\n'

        tools_code += f"""class {tool_name}Tool(BaseTool):
    name = "{tool_name.lower()}"
    description = "{tool_description}"
    
    def _run(self, {', '.join([arg.get("name", "arg") for arg in tool_args])}):
        \"\"\"Use the {tool_name} tool.\"\"\"
        # TODO: Implement the tool functionality
        return f"Using {tool_name} with {', '.join([arg.get("name", 'arg') + '=' + arg.get('name', 'arg') for arg in tool_args])}"
    
    def args_schema(self):
        return {{
{args_str}        }}

"""

    tools_code += """def get_tools() -> List[BaseTool]:
    \"\"\"Get all tools for the agent.\"\"\"
    return [
"""

    for tool in tools:
        tool_name = tool.get("name", "GenericTool")
        tools_code += f"        {tool_name}Tool(),\n"

    tools_code += """    ]
"""

    return tools_code


def generate_state_file():
    state_code = """from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

class AgentState(BaseModel):
    \"\"\"State for the agent.\"\"\"
    messages: List[BaseMessage] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    current_step: Optional[str] = None
    intermediate_steps: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: Dict[str, Any] = Field(default_factory=dict)
"""

    return state_code


def generate_nodes_file(agent_name, agent_prompt):
    nodes_code = f"""from typing import List, Dict, Any, Tuple, Optional
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from ..utils.state import AgentState
from ..utils.tools import get_tools

# Initialize the language model
model = ChatOpenAI(model="gpt-4-turbo")

# Define the agent prompt
AGENT_PROMPT = \"\"\"{agent_prompt}\"\"\"

def agent_prompt_template():
    return ChatPromptTemplate.from_messages([
        ("system", AGENT_PROMPT),
        ("human", "{{input}}"),
    ])

def get_conversation_history(state: AgentState) -> str:
    \"\"\"Get the conversation history as a string.\"\"\"
    messages = []
    for message in state.messages:
        if isinstance(message, HumanMessage):
            messages.append(f"Human: {{message.content}}")
        elif isinstance(message, AIMessage):
            messages.append(f"{agent_name}: {{message.content}}")
    return "\\n".join(messages)

def run_agent(state: AgentState, input: str) -> AgentState:
    \"\"\"Run the agent to process the input.\"\"\"
    human_message = HumanMessage(content=input)
    state.messages.append(human_message)
    
    # Create the prompt with conversation history
    prompt = agent_prompt_template()
    prompt_input = {{
        "input": input,
        "conversation_history": get_conversation_history(state),
        "tools": [t.name + ": " + t.description for t in get_tools()]
    }}
    
    # Run the agent
    response = model.invoke(prompt.format(**prompt_input))
    state.messages.append(response)
    
    return state

def process_tools(state: AgentState) -> AgentState:
    \"\"\"Process any tool calls from the agent.\"\"\"
    # TODO: Implement tool processing logic
    # This would parse the agent's response for tool calls
    # and execute the appropriate tools
    
    return state

def generate_response(state: AgentState) -> Tuple[AgentState, Dict[str, Any]]:
    \"\"\"Generate the final response to return to the user.\"\"\"
    # Get the most recent AI message
    most_recent_message = next((m for m in reversed(state.messages) if isinstance(m, AIMessage)), None)
    
    if most_recent_message:
        response = most_recent_message.content
    else:
        response = "I'm not sure how to respond."
    
    return state, {{"response": response}}
"""

    return nodes_code


def generate_agent_file(agent_name):
    agent_code = f"""from typing import Dict, Any, Tuple
from langgraph.graph import StateGraph, END
from {agent_name}.utils.state import AgentState
from {agent_name}.utils.nodes import run_agent, process_tools, generate_response

def create_agent_graph():
    \"\"\"Create the {agent_name} agent graph.\"\"\"
    # Initialize the graph
    graph = StateGraph(AgentState)
    
    # Define nodes
    graph.add_node("run_agent", run_agent)
    graph.add_node("process_tools", process_tools)
    graph.add_node("generate_response", generate_response)
    
    # Define edges
    graph.add_edge("run_agent", "process_tools")
    graph.add_edge("process_tools", "generate_response")
    graph.add_edge("generate_response", END)
    
    # Compile the graph
    return graph.compile()

def get_agent():
    \"\"\"Get the {agent_name} agent.\"\"\"
    return create_agent_graph()

def run_agent(input_text: str, state: Dict[str, Any] = None) -> Dict[str, Any]:
    \"\"\"Run the {agent_name} agent with the given input.\"\"\"
    agent = get_agent()
    
    # Initialize state if not provided
    if state is None:
        state = AgentState().dict()
    
    # Run the agent
    result = agent.invoke({{
        "messages": state.get("messages", []),
        "input": input_text,
    }})
    
    return result
"""

    return agent_code


def generate_requirements_file():
    return """langchain>=0.1.0
langgraph>=0.0.15
langchain-openai>=0.0.5
pydantic>=2.0.0
python-dotenv>=1.0.0
"""


def generate_env_file():
    return """# Add your API keys and environment variables here
OPENAI_API_KEY=your-openai-api-key
"""


def generate_langgraph_json(agent_name):
    config = {
        "dependencies": [f"./{agent_name}"],
        "graphs": {"agent": f"./{agent_name}/agent.py:graph"},
        "env": ".env",
    }

    return json.dumps(config, indent=2)


def create_project_structure(agent_config, output_dir="."):
    """Create the project structure based on the agent config."""
    agent_name = agent_config.get("name", "my_agent")
    sanitized_name = agent_name.replace(" ", "_").lower()
    agent_prompt = agent_config.get("prompt", "You are a helpful assistant.")
    tools = agent_config.get("tools", [])

    # Create the base directory
    base_dir = Path(output_dir)
    base_dir.mkdir(exist_ok=True)

    # Create the agent directory
    agent_dir = base_dir / sanitized_name
    agent_dir.mkdir(exist_ok=True)

    # Create the utils directory
    utils_dir = agent_dir / "utils"
    utils_dir.mkdir(exist_ok=True)

    # Create files
    (agent_dir / "__init__.py").write_text(generate_init_file())
    (agent_dir / "agent.py").write_text(generate_agent_file(sanitized_name))

    (utils_dir / "__init__.py").write_text(generate_init_file())
    (utils_dir / "tools.py").write_text(generate_tools_file(tools))
    (utils_dir / "state.py").write_text(generate_state_file())
    (utils_dir / "nodes.py").write_text(generate_nodes_file(agent_name, agent_prompt))

    (base_dir / ".env").write_text(generate_env_file())
    (base_dir / "requirements.txt").write_text(generate_requirements_file())
    (base_dir / "langgraph.json").write_text(generate_langgraph_json(sanitized_name))

    return sanitized_name


def main():
    parser = argparse.ArgumentParser(description="Generate a LangGraph agent project")
    parser.add_argument("--config", type=str, help="Path to the agent config JSON file")
    parser.add_argument(
        "--output", type=str, default="./example", help="Output directory"
    )

    args = parser.parse_args()

    # Load config
    if args.config:
        with open(args.config, "r") as f:
            agent_config = json.load(f)
    else:
        # Example config
        agent_config = {
            "name": "my_agent",
            "prompt": "You are a helpful assistant. You have access to several tools to help the user.",
            "tools": [
                {
                    "name": "Calculator",
                    "description": "Perform basic mathematical operations",
                    "args": [
                        {
                            "name": "expression",
                            "type": "str",
                            "description": "The mathematical expression to evaluate",
                        }
                    ],
                },
                {
                    "name": "WeatherCheck",
                    "description": "Get the current weather for a location",
                    "args": [
                        {
                            "name": "location",
                            "type": "str",
                            "description": "The location to check weather for",
                        }
                    ],
                },
            ],
        }

    # Create the project
    agent_name = create_project_structure(agent_config, args.output)
    print(f"Generated LangGraph agent project for '{agent_name}' in {args.output}")


if __name__ == "__main__":
    main()
