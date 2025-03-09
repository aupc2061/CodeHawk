from code_agent.main import run_agent

# Run the code agent with a natural language question/request
run_agent(
    question="Analyse the structure of the codebase",
    model="gemini",  # Currently supports "claude"
    temperature=0,
    workspace_dir=r"D:\Projects\llmpairprog\Agentless\get_repo_structure"   # Lower values for more deterministic responses
)