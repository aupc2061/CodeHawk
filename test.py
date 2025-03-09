from code_agent.main import run_agent

# Run the code agent with a natural language question/request
run_agent(
    question="Provide your question",
    model="model_name",  # Currently supports "claude, gemini, groq"
    temperature=0,
    workspace_dir=r"Your workspace dir"   # Lower values for more deterministic responses
)
