# Add these methods to your existing code_generator.py


def _generate_human_node_components(self, project_path: str) -> None:
    """Generate components needed for human-in-the-loop functionality"""
    # Generate the human node template
    template = self.env.get_template("human_node.py.j2")

    # Render and write to the utils directory
    content = template.render()
    with open(
        os.path.join(project_path, "my_agent", "utils", "human_nodes.py"), "w"
    ) as f:
        f.write(content)
