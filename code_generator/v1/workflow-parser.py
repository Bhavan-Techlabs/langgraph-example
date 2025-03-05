import logging
from typing import Dict, Any, List, Optional
import json


class WorkflowParser:
    """
    Parser to convert JSON workflow definitions into a structured format
    that can be used by the LangGraph code generator.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse(self, workflow_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the workflow JSON from the frontend into a structured format.

        Args:
            workflow_json: The JSON definition from the frontend

        Returns:
            A structured representation of the workflow
        """
        self.logger.info("Parsing workflow definition")

        try:
            # Extract basic workflow structure
            parsed_workflow = {
                "agents": self._extract_agents(workflow_json),
                "tools": self._extract_tools(workflow_json),
                "llms": self._extract_llms(workflow_json),
                "slms": self._extract_slms(workflow_json),
                "prompt_templates": self._extract_prompt_templates(workflow_json),
                "graph": self._extract_graph(workflow_json),
                "config": self._extract_config(workflow_json),
            }

            self.logger.debug(
                f"Parsed workflow: {json.dumps(parsed_workflow, indent=2)}"
            )
            return parsed_workflow

        except Exception as e:
            self.logger.error(f"Error parsing workflow: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to parse workflow: {str(e)}")

    def _extract_agents(self, workflow_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract agent definitions from the workflow JSON."""
        agents = []

        # If the workflow directly contains an agent definition
        if "agent" in workflow_json:
            agents.append(workflow_json["agent"])

        # If there's an agents array
        elif "agents" in workflow_json and isinstance(workflow_json["agents"], list):
            agents.extend(workflow_json["agents"])

        # Extract agent nodes from the graph if available
        if "graph" in workflow_json and "nodes" in workflow_json["graph"]:
            for node in workflow_json["graph"]["nodes"]:
                if (
                    node.get("type") == "agent"
                    and "data" in node
                    and "agent" in node["data"]
                ):
                    # Avoid duplicates
                    agent_id = node["data"]["agent"].get("id")
                    if not any(a.get("id") == agent_id for a in agents):
                        agents.append(node["data"]["agent"])

        return agents

    def _extract_tools(self, workflow_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool definitions from the workflow JSON."""
        tools = []

        # If the workflow directly contains a tool definition
        if "tool" in workflow_json:
            tools.append(workflow_json["tool"])

        # If there's a tools array
        elif "tools" in workflow_json and isinstance(workflow_json["tools"], list):
            tools.extend(workflow_json["tools"])

        # Extract tools from agents
        for agent in self._extract_agents(workflow_json):
            if "tools" in agent and isinstance(agent["tools"], list):
                for tool_ref in agent["tools"]:
                    # Find the actual tool definition if it's a reference
                    if "toolId" in tool_ref:
                        tool_id = tool_ref["toolId"]
                        # Check if we already have this tool
                        if not any(t.get("id") == tool_id for t in tools):
                            # If we have a tool registry in the workflow, look it up
                            if "toolRegistry" in workflow_json and isinstance(
                                workflow_json["toolRegistry"], dict
                            ):
                                for tool in workflow_json["toolRegistry"].values():
                                    if tool.get("id") == tool_id:
                                        tools.append(tool)
                                        break

        return tools

    def _extract_llms(self, workflow_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract LLM definitions from the workflow JSON."""
        llms = []

        # If the workflow directly contains an LLM definition
        if "llm" in workflow_json:
            llms.append(workflow_json["llm"])

        # If there's an llms array
        elif "llms" in workflow_json and isinstance(workflow_json["llms"], list):
            llms.extend(workflow_json["llms"])

        # Extract LLMs from agents
        for agent in self._extract_agents(workflow_json):
            if "llmId" in agent:
                llm_id = agent["llmId"]
                # Check if we already have this LLM
                if not any(l.get("id") == llm_id for l in llms):
                    # If we have an LLM registry in the workflow, look it up
                    if "llmRegistry" in workflow_json and isinstance(
                        workflow_json["llmRegistry"], dict
                    ):
                        for llm in workflow_json["llmRegistry"].values():
                            if llm.get("id") == llm_id:
                                llms.append(llm)
                                break

        return llms

    def _extract_slms(self, workflow_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract SLM definitions from the workflow JSON."""
        slms = []

        # If the workflow directly contains an SLM definition
        if "slm" in workflow_json:
            slms.append(workflow_json["slm"])

        # If there's an slms array
        elif "slms" in workflow_json and isinstance(workflow_json["slms"], list):
            slms.extend(workflow_json["slms"])

        # Extract SLMs from agents
        for agent in self._extract_agents(workflow_json):
            if "slmId" in agent:
                slm_id = agent["slmId"]
                # Check if we already have this SLM
                if not any(s.get("id") == slm_id for s in slms):
                    # If we have an SLM registry in the workflow, look it up
                    if "slmRegistry" in workflow_json and isinstance(
                        workflow_json["slmRegistry"], dict
                    ):
                        for slm in workflow_json["slmRegistry"].values():
                            if slm.get("id") == slm_id:
                                slms.append(slm)
                                break

        return slms

    def _extract_prompt_templates(
        self, workflow_json: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract prompt template definitions from the workflow JSON."""
        templates = []

        # If the workflow directly contains a prompt template definition
        if "promptTemplate" in workflow_json:
            templates.append(workflow_json["promptTemplate"])

        # If there's a promptTemplates array
        elif "promptTemplates" in workflow_json and isinstance(
            workflow_json["promptTemplates"], list
        ):
            templates.extend(workflow_json["promptTemplates"])

        # Extract prompt templates from agents
        for agent in self._extract_agents(workflow_json):
            if "promptTemplateId" in agent:
                template_id = agent["promptTemplateId"]
                # Check if we already have this template
                if not any(t.get("id") == template_id for t in templates):
                    # If we have a template registry in the workflow, look it up
                    if "promptTemplateRegistry" in workflow_json and isinstance(
                        workflow_json["promptTemplateRegistry"], dict
                    ):
                        for template in workflow_json[
                            "promptTemplateRegistry"
                        ].values():
                            if template.get("id") == template_id:
                                templates.append(template)
                                break

        return templates

    def _extract_graph(self, workflow_json: Dict[str, Any]) -> Dict[str, Any]:
        """Extract graph definition from the workflow JSON."""
        if "graph" in workflow_json:
            return workflow_json["graph"]
        return {"nodes": [], "edges": []}

    def _extract_config(self, workflow_json: Dict[str, Any]) -> Dict[str, Any]:
        """Extract configuration from the workflow JSON."""
        config = {}

        # Extract specific configuration fields
        for key in ["name", "description", "version"]:
            if key in workflow_json:
                config[key] = workflow_json[key]

        # Extract key vault references
        if "keyVault" in workflow_json:
            config["keyVault"] = workflow_json["keyVault"]

        return config
