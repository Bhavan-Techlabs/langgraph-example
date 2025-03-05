from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

# Abstract base class for agent frameworks
class AgentFrameworkAdapter(ABC):
    """
    Abstract base class defining the interface for agent framework adapters
    """
    @abstractmethod
    def create_agent(
        self, 
        agent_config: Dict[str, Any], 
        tools: Optional[List[Any]] = None,
        llm: Optional[Any] = None
    ) -> Any:
        """
        Create an agent using the specific framework's implementation
        
        :param agent_config: Configuration dictionary for the agent
        :param tools: Optional list of tools for the agent
        :param llm: Optional language model for the agent
        :return: Instantiated agent
        """
        pass

    @abstractmethod
    def create_workflow(
        self, 
        workflow_config: Dict[str, Any], 
        agents: List[Any]
    ) -> Any:
        """
        Create a workflow using the specific framework's implementation
        
        :param workflow_config: Configuration for the entire workflow
        :param agents: List of agents to be used in the workflow
        :return: Instantiated workflow
        """
        pass

# Adapter for LangGraph
class LangGraphAdapter(AgentFrameworkAdapter):
    def create_agent(
        self, 
        agent_config: Dict[str, Any], 
        tools: Optional[List[Any]] = None,
        llm: Optional[Any] = None
    ) -> Any:
        from langchain_core.language_models import BaseLanguageModel
        from langchain_core.tools import BaseTool
        from langgraph.prebuilt import create_react_agent
        
        # Use provided LLM or default to OpenAI
        if llm is None:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=agent_config.get('llm', {}).get('model', 'gpt-4'),
                temperature=agent_config.get('llm', {}).get('temperature', 0.7)
            )
        
        # Validate LLM type
        if not isinstance(llm, BaseLanguageModel):
            raise ValueError("Invalid LLM provided. Must be a BaseLanguageModel.")
        
        # Prepare tools
        if tools is None:
            tools = []
        
        # Validate tools
        validated_tools = []
        for tool in tools:
            if not isinstance(tool, BaseTool):
                raise ValueError(f"Invalid tool: {tool}. Must be a BaseTool.")
            validated_tools.append(tool)
        
        # Create agent based on type
        agent_type = agent_config.get('type', 'react')
        if agent_type.lower() == 'react':
            return create_react_agent(llm, validated_tools)
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")

    def create_workflow(
        self, 
        workflow_config: Dict[str, Any], 
        agents: List[Any]
    ) -> Any:
        from langgraph.graph import StateGraph, MessagesState
        
        # Create state based on workflow configuration
        state_class = workflow_config.get('state_class', MessagesState)
        
        # Initialize workflow builder
        builder = StateGraph(state_class)
        
        # Add nodes and configure edges (simplified example)
        for agent in agents:
            builder.add_node(agent.__class__.__name__, agent)
        
        # Configure default linear workflow
        # You'd customize this based on specific workflow needs
        for i in range(len(agents) - 1):
            builder.add_edge(agents[i].__class__.__name__, agents[i+1].__class__.__name__)
        
        return builder.compile()

# Adapter for AutoGen (placeholder)
class AutoGenAdapter(AgentFrameworkAdapter):
    def create_agent(
        self, 
        agent_config: Dict[str, Any], 
        tools: Optional[List[Any]] = None,
        llm: Optional[Any] = None
    ) -> Any:
        try:
            import autogen
        except ImportError:
            raise ImportError("AutoGen library is not installed. Please install it first.")
        
        # Placeholder implementation
        # You would need to implement actual agent creation logic
        agent_type = agent_config.get('type', 'assistant')
        
        if agent_type == 'assistant':
            return autogen.AssistantAgent(
                name=agent_config.get('name', 'Assistant'),
                llm_config={"config_list": [{"model": "gpt-4"}]}
            )
        elif agent_type == 'user':
            return autogen.UserProxyAgent(
                name=agent_config.get('name', 'User'),
                human_input_mode="ALWAYS"
            )
        
        raise ValueError(f"Unsupported AutoGen agent type: {agent_type}")

    def create_workflow(
        self, 
        workflow_config: Dict[str, Any], 
        agents: List[Any]
    ) -> Any:
        # Placeholder for workflow creation
        # In AutoGen, this might involve setting up groupchats or specific interaction patterns
        try:
            import autogen
        except ImportError:
            raise ImportError("AutoGen library is not installed. Please install it first.")
        
        return autogen.GroupChat(agents=agents, messages=[])

# Agent Framework Factory
class AgentFrameworkFactory:
    """
    Factory for creating agents and workflows across different frameworks
    """
    _adapters: Dict[str, Type[AgentFrameworkAdapter]] = {
        'langgraph': LangGraphAdapter,
        'autogen': AutoGenAdapter
    }

    @classmethod
    def register_framework(
        cls, 
        framework_name: str, 
        adapter_class: Type[AgentFrameworkAdapter]
    ):
        """
        Register a new agent framework adapter
        
        :param framework_name: Name of the framework
        :param adapter_class: Adapter class for the framework
        """
        cls._adapters[framework_name.lower()] = adapter_class

    @classmethod
    def create_agent(
        cls, 
        framework: str, 
        agent_config: Dict[str, Any], 
        tools: Optional[List[Any]] = None,
        llm: Optional[Any] = None
    ) -> Any:
        """
        Create an agent using the specified framework
        
        :param framework: Name of the agent framework
        :param agent_config: Configuration for the agent
        :param tools: Optional list of tools
        :param llm: Optional language model
        :return: Instantiated agent
        """
        framework = framework.lower()
        if framework not in cls._adapters:
            raise ValueError(f"Unsupported framework: {framework}")
        
        adapter = cls._adapters[framework]()
        return adapter.create_agent(agent_config, tools, llm)

    @classmethod
    def create_workflow(
        cls, 
        framework: str, 
        workflow_config: Dict[str, Any], 
        agents: List[Any]
    ) -> Any:
        """
        Create a workflow using the specified framework
        
        :param framework: Name of the agent framework
        :param workflow_config: Configuration for the workflow
        :param agents: List of agents to be used in the workflow
        :return: Instantiated workflow
        """
        framework = framework.lower()
        if framework not in cls._adapters:
            raise ValueError(f"Unsupported framework: {framework}")
        
        adapter = cls._adapters[framework]()
        return adapter.create_workflow(workflow_config, agents)

# Example usage
def example_usage():
    # Example configuration
    agent_config = {
        'name': 'Research Assistant',
        'type': 'react',
        'llm': {
            'model': 'gpt-4',
            'temperature': 0.7
        }
    }
    
    # Create tools (example)
    from langchain_core.tools import tool
    
    @tool
    def search_tool(query: str):
        """Search for information online."""
        return f"Results for query: {query}"
    
    # Create an agent using LangGraph
    langgraph_agent = AgentFrameworkFactory.create_agent(
        framework='langgraph', 
        agent_config=agent_config,
        tools=[search_tool]
    )
    
    # Create a workflow
    workflow = AgentFrameworkFactory.create_workflow(
        framework='langgraph',
        workflow_config={},
        agents=[langgraph_agent]
    )
    
    print("Agent and Workflow created successfully!")

# Optional: Add more framework adapters as needed
# Example of how to add a new framework
class LlamaIndexAdapter(AgentFrameworkAdapter):
    def create_agent(self, *args, **kwargs):
        # Placeholder for LlamaIndex agent creation
        raise NotImplementedError("LlamaIndex adapter not fully implemented")
    
    def create_workflow(self, *args, **kwargs):
        # Placeholder for LlamaIndex workflow creation
        raise NotImplementedError("LlamaIndex adapter not fully implemented")

# Register the new framework (optional)
AgentFrameworkFactory.register_framework('llamaindex', LlamaIndexAdapter)
