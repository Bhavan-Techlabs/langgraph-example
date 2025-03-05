# Add these methods to your existing execution_manager.py file


def pause_execution(self, workflow_execution_id: int, node_execution_id: int) -> bool:
    """Pause a workflow execution at a specific node"""
    # Get the workflow execution
    execution = (
        self.db.query(WorkflowExecution)
        .filter(WorkflowExecution.id == workflow_execution_id)
        .first()
    )

    if not execution or execution.status not in ["RUNNING", "CREATED"]:
        return False

    # Update workflow execution status
    execution.status = "PAUSED"

    # Update node execution status if provided
    if node_execution_id:
        node_execution = (
            self.db.query(NodeExecution)
            .filter(NodeExecution.id == node_execution_id)
            .first()
        )

        if node_execution:
            node_execution.status = "PAUSED"

    self.db.commit()
    return True


def resume_execution(
    self,
    workflow_execution_id: int,
    node_execution_id: int,
    intervention_request_id: Optional[int] = None,
) -> bool:
    """Resume a paused workflow execution"""
    # Get the workflow execution
    execution = (
        self.db.query(WorkflowExecution)
        .filter(WorkflowExecution.id == workflow_execution_id)
        .first()
    )

    if not execution or execution.status != "PAUSED":
        return False

    # Update workflow execution status
    execution.status = "RUNNING"

    # Update metadata to include human intervention info
    metadata = execution.metadata or {}

    if intervention_request_id:
        # Get the intervention request and response
        request = (
            self.db.query(HumanInterventionRequest)
            .filter(HumanInterventionRequest.id == intervention_request_id)
            .first()
        )

        response = (
            self.db.query(HumanInterventionResponse)
            .filter(HumanInterventionResponse.request_id == intervention_request_id)
            .first()
        )

        if request and response:
            interventions = metadata.get("human_interventions", [])
            interventions.append(
                {
                    "request_id": intervention_request_id,
                    "node_execution_id": node_execution_id,
                    "requested_at": request.created_at.isoformat(),
                    "responded_at": response.created_at.isoformat(),
                    "response_data": response.response_data,
                    "notes": response.notes,
                }
            )
            metadata["human_interventions"] = interventions

    execution.metadata = metadata

    # Update node execution status
    if node_execution_id:
        node_execution = (
            self.db.query(NodeExecution)
            .filter(NodeExecution.id == node_execution_id)
            .first()
        )

        if node_execution:
            node_execution.status = "COMPLETED"

    self.db.commit()

    # Re-run the execution from the current point
    # This will pick up where it left off
    self.db.refresh(execution)
    self.run_execution(workflow_execution_id, resume=True)

    return True


def run_execution(self, execution_id: int, resume: bool = False) -> None:
    """Run or resume a workflow execution"""
    # Update the existing run_execution method to handle resuming
    execution = self.get_execution(execution_id)
    if not execution:
        return

    # Skip if not in a runnable state
    if execution.status not in ["CREATED", "RUNNING"] and not resume:
        return

    # Update status to running
    if execution.status != "RUNNING":
        execution.status = "RUNNING"
        self.db.commit()

    try:
        # Dynamically import and run the generated agent code
        project_path = get_project_path(execution.workflow_id)
        agent_module_path = os.path.join(project_path, "my_agent", "agent.py")

        # Load the agent module
        spec = importlib.util.spec_from_file_location(
            "dynamic_agent", agent_module_path
        )
        agent_module = importlib.util.module_from_spec(spec)
        sys.modules["dynamic_agent"] = agent_module
        spec.loader.exec_module(agent_module)

        # Run the agent with input data
        try:
            # Get the graph and state
            graph = agent_module.get_graph()

            # If resuming, get the current state from the latest node execution
            if resume:
                # Find the last completed node execution to get its output state
                last_node = (
                    self.db.query(NodeExecution)
                    .filter(
                        NodeExecution.workflow_execution_id == execution_id,
                        NodeExecution.status == "COMPLETED",
                    )
                    .order_by(NodeExecution.finished_at.desc())
                    .first()
                )

                if last_node and last_node.output_data:
                    # Use the last state as the input
                    input_data = last_node.output_data
                else:
                    # Fall back to the original input
                    input_data = execution.input_data
            else:
                # Use the original input data
                input_data = execution.input_data

            # Set up execution tracking callbacks
            def node_callback(event):
                """Callback for node execution events"""
                if event["type"] == "node:start":
                    node_id = self._get_node_id_by_name(
                        event["node_name"], execution.workflow_id
                    )

                    # Check if this is a human node type
                    is_human_node = self._is_human_node(node_id)

                    node_exec = NodeExecution(
                        workflow_execution_id=execution_id,
                        node_id=node_id,
                        status="RUNNING",
                        started_at=datetime.now(),
                        input_data=event.get("inputs", {}),
                    )
                    self.db.add(node_exec)
                    self.db.commit()
                    self.db.refresh(node_exec)

                    # If this is a human node, automatically create an intervention request
                    if is_human_node:
                        from human_intervention_manager import HumanInterventionManager

                        # Pause the workflow execution
                        self.pause_execution(execution_id, node_exec.id)

                        # Create an intervention request
                        intervention_manager = HumanInterventionManager(self.db)
                        intervention_manager.create_intervention_request(
                            node_execution_id=node_exec.id,
                            prompt=f"Human approval required for node: {event['node_name']}",
                            context_data=event.get("inputs", {}),
                            options=None,  # Could be extracted from node config
                            priority=1,
                            expires_in_minutes=60,
                        )

                        # Stop graph execution
                        raise RuntimeError("Workflow paused for human intervention")

                elif event["type"] == "node:end":
                    node_exec = (
                        self.db.query(NodeExecution)
                        .filter(
                            NodeExecution.workflow_execution_id == execution_id,
                            NodeExecution.node_id
                            == self._get_node_id_by_name(
                                event["node_name"], execution.workflow_id
                            ),
                            NodeExecution.status == "RUNNING",
                        )
                        .first()
                    )

                    if node_exec:
                        node_exec.status = "COMPLETED"
                        node_exec.finished_at = datetime.now()
                        node_exec.output_data = event.get("outputs", {})
                        self.db.commit()

            # Register callback
            graph.add_listener(node_callback)

            # Execute the graph
            result = graph.invoke(input_data)

            # Update execution status
            execution.status = "COMPLETED"
            execution.finished_at = datetime.now()
            execution.output_data = result
            self.db.commit()

        except Exception as e:
            # Special case for human intervention
            if str(e) == "Workflow paused for human intervention":
                # Already handled by the callback
                return

            # Handle agent execution errors
            execution.status = "FAILED"
            execution.finished_at = datetime.now()
            execution.output_data = {
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
            self.db.commit()

            # Also update any running node executions
            running_nodes = (
                self.db.query(NodeExecution)
                .filter(
                    NodeExecution.workflow_execution_id == execution_id,
                    NodeExecution.status == "RUNNING",
                )
                .all()
            )

            for node in running_nodes:
                node.status = "FAILED"
                node.finished_at = datetime.now()
                node.error = str(e)

            self.db.commit()

    except Exception as e:
        # Handle system-level errors
        execution.status = "ERROR"
        execution.finished_at = datetime.now()
        execution.output_data = {"error": str(e), "traceback": traceback.format_exc()}
        self.db.commit()


def _is_human_node(self, node_id: int) -> bool:
    """Check if a node is a human-in-the-loop node"""
    from models import Node

    node = self.db.query(Node).filter(Node.id == node_id).first()
    return node and node.is_human_node
