import argparse
from code_agent.main import run_agent
from rich import print
from rich.prompt import Prompt

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Run the code agent with a natural language request.")
    parser.add_argument("-q", "--question", type=str, help="The natural language request for the agent")
    parser.add_argument("-m", "--model", type=str, help="The model to use")  # No default here!

    # Parse arguments
    args = parser.parse_args()

    # If question is not provided via CLI, prompt interactively
    if not args.question:
        args.question = Prompt.ask("[bold cyan]Enter your request[/]")

    # If model is not provided, prompt interactively with default value
    if not args.model:
        args.model = Prompt.ask("[bold cyan]Enter model name[/]", default="gemini")

    print("\n[bold green]Running Code Agent...[/]")
    print(f"[bold yellow]Question:[/] {args.question}")
    print(f"[bold yellow]Model:[/] {args.model}\n")

    # Run the agent with provided input
    run_agent(question=args.question, model=args.model, temperature=0)

if __name__ == "__main__":
    main()
