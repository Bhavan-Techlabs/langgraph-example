# LangGraph Cloud Example

This is an example agent to deploy with LangGraph Cloud.

[LangGraph](https://github.com/langchain-ai/langgraph) is a library for building stateful, multi-actor applications with LLMs. The main use cases for LangGraph are conversational agents, and long-running, multi-step LLM applications or any LLM application that would benefit from built-in support for persistent checkpoints, cycles and human-in-the-loop interactions (ie. LLM and human collaboration).

LangGraph shortens the time-to-market for developers using LangGraph, with a one-liner command to start a production-ready HTTP microservice for your LangGraph applications, with built-in persistence. This lets you focus on the logic of your LangGraph graph, and leave the scaling and API design to us. The API is inspired by the OpenAI assistants API, and is designed to fit in alongside your existing services.

In order to deploy this agent to LangGraph Cloud you will want to first fork this repo. After that, you can follow the instructions [here](https://langchain-ai.github.io/langgraph/cloud/) to deploy to LangGraph Cloud.

## Setup

brew install langgraph-cli
langgraph build -t my-image
docker compose up

Once the API is running, interact with that using

https://langchain-ai.github.io/langgraph/cloud/reference/api/api_ref.html#tag/assistants

## Links

To self host: https://langchain-ai.github.io/langgraph/how-tos/deploy-self-hosted/

Structure of the application: https://langchain-ai.github.io/langgraph/concepts/application_structure/

Local server setup: https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/#developer-references

Hot reloading: https://langchain-ai.github.io/langgraph/concepts/langgraph_cli/#dev