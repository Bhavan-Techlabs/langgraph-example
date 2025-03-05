import sys
from langgraph.graph import StateGraph, START, END, Command
from langchain_core.messages import HumanMessage
from typing import Any, Dict, Callable

# Define our State type simply as a dictionary
State = Dict[str, Any]


# --- Supervisor Node Function ---
def supervisor_node(state: State) -> Command:
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the following workers: "
        "researcher, coder. Given the user request, respond with the worker to act next. When finished, respond with FINISH."
    )
    # Prepend the system prompt to the current messages
    messages = [{"role": "system", "content": system_prompt}] + state.get(
        "messages", []
    )

    # Simulate an LLM call to decide the next agent (in production, call the actual LLM)
    # For demonstration, we always choose "researcher"
    response = {"next": "researcher"}
    goto = response["next"]
    if goto == "FINISH":
        goto = END
    return Command(goto=goto, update={"next": goto})


# --- Generic Agent Node Function ---
def agent_node(state: State, node_config: Dict[str, Any]) -> Command:
    # Retrieve the prompt template content from the node config
    prompt = node_config.get("promptTemplate", {}).get(
        "content", "Default agent prompt"
    )

    # Simulate a call to the agent's LLM (embedded in node_config["llm"]) and process tools if needed.
    # In a real implementation, you'd invoke the agent (e.g., research_agent or code_agent) here.
    new_message = {
        "role": "agent",
        "content": f"Processed by agent using prompt: {prompt}",
    }
    updated_messages = state.get("messages", []) + [new_message]
    # For simplicity, we route back to the supervisor
    return Command(goto="supervisor", update={"messages": updated_messages})


# --- Utility: Map string value to graph constants ---
def map_node_value(value: str):
    if value == "START":
        return START
    elif value == "END":
        return END
    return value


# --- Generate Graph Builder ---
def generate_builder(workflow_config: Dict[str, Any]) -> StateGraph:
    # Create a new StateGraph instance (using a simple dict as our state)
    builder = StateGraph(dict)
    nodes = workflow_config["nodes"]
    edges = workflow_config["edges"]

    # Add each node to the graph
    for node in nodes:
        node_id = node["id"]
        node_type = node["type"]

        if node_type == "supervisor_agent":
            # Use the supervisor_node function directly
            action = supervisor_node
        elif node_type == "agent":
            # For agent nodes, bind the node's config via a lambda
            action = lambda state, config=node["config"]: agent_node(state, config)
        else:
            # Default to a no-op if unknown type
            action = lambda state: state

        builder.add_node(node_id, action)

    # Add edges to the graph
    for edge in edges:
        source = map_node_value(edge["source"])
        target = map_node_value(edge["target"])
        edge_type = edge.get("type", "auto")
        if edge_type in ["auto", "normal"]:
            builder.add_edge(source, target)
        elif edge_type == "conditional":
            # For conditional edges, you might implement a routing function; here we simply route to the target.
            routing_func = lambda state, target=target: target
            builder.add_conditional_edges(source, routing_func, target)
        else:
            builder.add_edge(source, target)

    return builder


# --- Example Usage ---
if __name__ == "__main__":
    # This is an abbreviated version of your rich workflow JSON.
    # In practice, load this JSON from a file or API.
    workflow_json = {
        "workflow_metadata": {
            "workflow_id": "wf_001",
            "workspace_id": "ws_001",
            "name": "AI Workflow with Router Logic",
            "description": "A workflow where a supervisor agent routes tasks among specialized agents.",
            "version": "1.0",
            "created_date": "2025-03-02T00:00:00Z",
            "updated_date": "2025-03-02T00:00:00Z",
        },
        "nodes": [
            {
                "id": "component_1",
                "type": "supervisor_agent",
                "label": "Supervisor Agent",
                "config": {
                    "llm": {
                        "id": "llm-001",
                        "name": "GPT-4",
                        "provider": "OpenAI",
                        "apiKeyId": "key-001",
                        "customConfig": {
                            "temperature": 0.7,
                            "max_tokens": 2048,
                            "top_p": 1.0,
                            "frequency_penalty": 0,
                            "presence_penalty": 0,
                            "model_name": "gpt-4",
                            "system_message": "You are ChatGPT.",
                            "streaming": False,
                        },
                        "realmId": "realm-01",
                        "isActive": True,
                        "isDeleted": False,
                        "createdBy": "user-001",
                        "updatedBy": None,
                    },
                    "promptTemplate": {
                        "id": "pt-001",
                        "templateKey": "system-default",
                        "content": "You are a helpful assistant. {{instruction}}",
                        "variables": {"instruction": "Provide concise answers"},
                        "category": "system",
                        "metadata": {
                            "description": "Default prompt for supervisor tasks"
                        },
                        "version": 1,
                        "realmId": "realm-01",
                        "isActive": True,
                        "isDeleted": False,
                        "createdBy": "user-001",
                        "updatedBy": None,
                    },
                    "team": [
                        {
                            "id": "component_2",
                            "specialization": "Handles external API data retrieval",
                            "agent": {
                                "id": "component_2",
                                "type": "agent",
                                "label": "API Handling Agent",
                            },
                        },
                        {
                            "id": "component_3",
                            "specialization": "Handles calculations and data processing",
                            "agent": {
                                "id": "component_3",
                                "type": "agent",
                                "label": "API Tool Node",
                            },
                        },
                    ],
                },
                "layout": {
                    "position": {"left": 100, "top": 100},
                    "dimensions": {"width": 180, "height": 64},
                    "is_locked": False,
                },
            },
            {
                "id": "component_2",
                "type": "agent",
                "label": "API Handling Agent",
                "config": {
                    "llm": {
                        "id": "llm-001",
                        "name": "GPT-4",
                        "provider": "OpenAI",
                        "apiKeyId": "key-001",
                        "customConfig": {
                            "temperature": 0.7,
                            "max_tokens": 2048,
                            "top_p": 1.0,
                            "frequency_penalty": 0,
                            "presence_penalty": 0,
                            "model_name": "gpt-4",
                            "system_message": "You are ChatGPT.",
                            "streaming": False,
                        },
                        "realmId": "realm-01",
                        "isActive": True,
                        "isDeleted": False,
                        "createdBy": "user-001",
                        "updatedBy": None,
                    },
                    "promptTemplate": {
                        "id": "pt-002",
                        "templateKey": "api-default",
                        "content": "You are an API handler. Fetch and process data accordingly.",
                        "variables": {},
                        "category": "api",
                        "metadata": {"description": "Prompt for API data retrieval"},
                        "version": 1,
                        "realmId": "realm-01",
                        "isActive": True,
                        "isDeleted": False,
                        "createdBy": "user-002",
                        "updatedBy": None,
                    },
                    "tools": [
                        {
                            "tool": {
                                "id": "tool-001",
                                "name": "Doc Retrieval",
                                "type": "RAG_Retrieval",
                                "description": "Retrieves documents from an external API",
                                "icon": "doc_icon.png",
                                "realmId": "realm-01",
                                "isActive": True,
                                "isDeleted": False,
                                "createdBy": "user-001",
                                "updatedBy": None,
                                "toolAPI": {
                                    "id": "api-001",
                                    "toolId": "tool-001",
                                    "method": "GET",
                                    "inputConfigs": {
                                        "url": "https://api.weather.com/v1",
                                        "headers": {
                                            "Authorization": "Bearer xxxxxxx",
                                            "Accept": "application/json",
                                        },
                                        "body": {"query": "search text"},
                                        "timeout": 30,
                                    },
                                    "numberOfResults": 3,
                                    "responseMapping": {
                                        "docField": "content",
                                        "metadataField": "meta",
                                    },
                                    "version": "1.0",
                                    "realmId": "realm-01",
                                    "isActive": True,
                                    "isDeleted": False,
                                    "createdBy": "user-001",
                                    "updatedBy": None,
                                },
                                "toolRAG": {
                                    "id": "rag-001",
                                    "toolId": "tool-001",
                                    "type": "faiss",
                                    "config": {
                                        "k": 5,
                                        "embedding_model": "openai-embedding-ada-002",
                                        "similarity_metric": "cosine",
                                        "chunk_size": 100,
                                        "index_path": "/path/to/faiss/index",
                                    },
                                    "version": 1,
                                    "realmId": "realm-01",
                                    "isActive": True,
                                    "isDeleted": False,
                                    "createdBy": "user-001",
                                    "updatedBy": None,
                                },
                            },
                            "config": {},
                            "hitl": {
                                "enabled": False,
                                "display_message": None,
                                "stage": None,
                            },
                        }
                    ],
                },
                "layout": {
                    "position": {"left": 300, "top": 100},
                    "dimensions": {"width": 180, "height": 64},
                    "is_locked": False,
                },
            },
            {
                "id": "component_3",
                "type": "agent",
                "label": "API Tool Node",
                "config": {
                    "llm": {
                        "id": "llm-001",
                        "name": "GPT-4",
                        "provider": "OpenAI",
                        "apiKeyId": "key-001",
                        "customConfig": {
                            "temperature": 0.7,
                            "max_tokens": 2048,
                            "top_p": 1.0,
                            "frequency_penalty": 0,
                            "presence_penalty": 0,
                            "model_name": "gpt-4",
                            "system_message": "You are ChatGPT.",
                            "streaming": False,
                        },
                        "realmId": "realm-01",
                        "isActive": True,
                        "isDeleted": False,
                        "createdBy": "user-001",
                        "updatedBy": None,
                    },
                    "promptTemplate": {
                        "id": "pt-003",
                        "templateKey": "api-tool",
                        "content": "You are an API tool node. Process the input data and send results.",
                        "variables": {},
                        "category": "tool",
                        "metadata": {
                            "description": "Prompt for API tool node operations"
                        },
                        "version": 1,
                        "realmId": "realm-01",
                        "isActive": True,
                        "isDeleted": False,
                        "createdBy": "user-003",
                        "updatedBy": None,
                    },
                    "tools": [
                        {
                            "tool": {
                                "id": "tool-001",
                                "name": "Doc Retrieval",
                                "type": "RAG_Retrieval",
                                "description": "Retrieves and posts document data",
                                "icon": "doc_icon.png",
                                "realmId": "realm-01",
                                "isActive": True,
                                "isDeleted": False,
                                "createdBy": "user-001",
                                "updatedBy": None,
                                "toolAPI": {
                                    "id": "api-002",
                                    "toolId": "tool-001",
                                    "method": "POST",
                                    "inputConfigs": {
                                        "url": "https://api.weather.com/v1",
                                        "headers": {
                                            "Authorization": "Bearer xxxxxxx",
                                            "Accept": "application/json",
                                        },
                                        "body": [
                                            {
                                                "field": "location",
                                                "type": "text",
                                                "description": "Location for weather data",
                                                "required": True,
                                            },
                                            {
                                                "field": "temp",
                                                "type": "number",
                                                "description": "Temperature value",
                                                "required": True,
                                            },
                                        ],
                                        "timeout": 30,
                                    },
                                    "numberOfResults": 1,
                                    "responseMapping": None,
                                    "version": "1.0",
                                    "realmId": "realm-01",
                                    "isActive": True,
                                    "isDeleted": False,
                                    "createdBy": "user-001",
                                    "updatedBy": None,
                                },
                                "toolRAG": {
                                    "id": "rag-002",
                                    "toolId": "tool-001",
                                    "type": "faiss",
                                    "config": {
                                        "k": 5,
                                        "embedding_model": "openai-embedding-ada-002",
                                        "similarity_metric": "cosine",
                                        "chunk_size": 100,
                                        "index_path": "/path/to/faiss/index",
                                    },
                                    "version": 1,
                                    "realmId": "realm-01",
                                    "isActive": True,
                                    "isDeleted": False,
                                    "createdBy": "user-001",
                                    "updatedBy": None,
                                },
                            },
                            "config": {},
                            "hitl": {"enabled": False, "stage": "before"},
                        }
                    ],
                },
                "layout": {
                    "position": {"left": 500, "top": 100},
                    "dimensions": {"width": 180, "height": 64},
                    "is_locked": False,
                },
            },
        ],
        "edges": [
            {"source": "component_1", "target": "component_2", "type": "auto"},
            {"source": "component_1", "target": "component_3", "type": "auto"},
        ],
    }

    # Build the graph from the JSON workflow
    graph = generate_builder(workflow_json)
    # Now you can compile and execute the graph as needed
    # For example: compiled_graph = graph.compile()
    # And then run: compiled_graph.run(initial_state)
    print("Graph built successfully.")
