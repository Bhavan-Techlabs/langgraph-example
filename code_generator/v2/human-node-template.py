# templates/human_node.py.j2
"""
Human intervention node template for LangGraph workflows.
This allows workflows to pause and await human input before proceeding.
"""
from typing import Dict, Any, Optional
import time
import asyncio
from datetime import datetime, timedelta

from langchain.schema import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from my_agent.utils.state import State


class HumanInterventionRequest(BaseModel):
    """Schema for a human intervention request"""

    request_id: str = Field(description="Unique identifier for the request")
    node_name: str = Field(description="Name of the node requesting intervention")
    workflow_execution_id: str = Field(description="ID of the workflow execution")
    context: Dict[str, Any] = Field(description="Context data for the human to review")
    prompt: str = Field(description="Prompt or question for the human")
    options: Optional[Dict[str, str]] = Field(
        default=None, description="Optional response options"
    )
    timeout_seconds: int = Field(default=3600, description="Timeout in seconds")
    created_at: datetime = Field(default_factory=datetime.now)


class HumanInterventionResponse(BaseModel):
    """Schema for a human intervention response"""

    request_id: str = Field(description="Reference to the request ID")
    response: Any = Field(description="Human response data")
    feedback: Optional[str] = Field(default=None, description="Optional feedback")
    approved: bool = Field(
        default=True, description="Whether the human approved the action"
    )
    responded_at: datetime = Field(default_factory=datetime.now)


async def human_intervention_node(
    state: State, config: Optional[RunnableConfig] = None, **kwargs
) -> Dict[str, Any]:
    """
    A LangGraph node that pauses execution and waits for human input.

    This function:
    1. Creates a human intervention request
    2. Polls for a response
    3. Returns the response when received

    Parameters:
    - state: The current state object
    - config: Configuration for the node

    Returns:
    - Updated state with human response
    """
    # Extract node configuration
    node_name = kwargs.get("node_name", "human_intervention")
    prompt = kwargs.get("prompt", "Human input required. Please review and respond.")
    timeout_seconds = kwargs.get("timeout", 3600)
    options = kwargs.get("options", None)

    # Create request model
    request = HumanInterventionRequest(
        request_id=f"req_{int(time.time())}",
        node_name=node_name,
        workflow_execution_id=config.get("execution_id", "unknown"),
        context=state.dict(),
        prompt=prompt,
        options=options,
        timeout_seconds=timeout_seconds,
    )

    # Create intervention request in database
    # In a real implementation, this would call an API to create the request
    # and notify relevant users (e.g., through websockets, email, etc.)
    print(f"Human intervention requested: {request.prompt}")
    print(f"Waiting for response (timeout: {timeout_seconds}s)...")

    # Poll for response
    # In production, this would be implemented with a proper async pattern,
    # possibly using websockets or a message queue
    start_time = time.time()
    response = None

    while time.time() - start_time < timeout_seconds:
        # Check if response exists - in a real implementation, this would query the database
        # For this example, we'll simulate a response after a short delay
        await asyncio.sleep(5)  # Simulated delay for demo purposes

        # Simulated response (in production, this would come from the database)
        if time.time() - start_time > 10:  # Simulate response after 10 seconds
            response = HumanInterventionResponse(
                request_id=request.request_id,
                response="Approved",
                feedback="Looks good to proceed.",
                approved=True,
            )
            break

    # Handle timeout
    if response is None:
        print("Human intervention request timed out!")
        # In a real implementation, you might want to handle the timeout differently
        # For example, proceed with a default action or raise an exception

        # For this example, we'll create a timeout response
        response = HumanInterventionResponse(
            request_id=request.request_id,
            response="TIMEOUT",
            feedback="Request timed out after waiting for human input.",
            approved=False,
        )

    # Update state with human response
    state_dict = state.dict()
    state_dict.update(
        {"human_intervention": {"request": request.dict(), "response": response.dict()}}
    )

    # Add message to message history if it exists
    if hasattr(state, "messages") and isinstance(state.messages, list):
        state_dict["messages"].append(
            HumanMessage(content=f"Human feedback: {response.response}")
        )

    return state_dict
