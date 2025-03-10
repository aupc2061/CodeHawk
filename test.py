import argparse
from code_agent.main import run_agent
from rich import print
from rich.prompt import Prompt
from rich.panel import Panel
from rich.align import Align
from rich.console import Console
from rich.table import Table

console = Console()

def main():
    # Display a perfectly aligned welcome message
    welcome_message = Panel(
        Align.center(
            "[bold cyan]🤖  Welcome to GitHub Code Agent!  🚀[/]\n"
            "──────────────────────────────────────────\n"
            "[bold white]An AI-powered tool to help you manage your GitHub repositories effortlessly.[/]\n\n"
            "[bold yellow]✨ What can this tool do? ✨[/]\n"
            "🔍 Debug issues in your codebase\n"
            "✍️ Modify or replace code snippets\n"
            "🧪 Write and optimize test cases\n"
            "📂 Handle README updates and repo maintenance\n"
            "⚡ Automate tedious GitHub tasks with AI\n\n"
            "[bold yellow]🤖  Supported AI Models:[/]\n"
            "🦙  [bold green]LLaMA[/]   - Open-source and efficient\n"
            "🔮  [bold blue]Gemini[/]  - Google’s advanced AI\n"
            "📝  [bold magenta]Claude[/]  - Anthropic’s high-quality text AI\n\n"
            "[bold green]Just enter your request, select a model, and let AI do the rest![/]\n",
            vertical="middle"
        ),
        title="[bold magenta]  AI-Powered GitHub Assistant  [/]",
        border_style="blue",
        width=80  # Ensuring consistent width for a clean right edge
    )
    
    console.print("\n")
    console.print(Align.center(welcome_message))
    console.print("\n")

    # Create an argument parser
    parser = argparse.ArgumentParser(description="Run the GitHub Code Agent with a natural language request.")
    parser.add_argument("-q", "--question", type=str, help="The natural language request for the agent")
    parser.add_argument("-m", "--model", type=str, help="The model to use (Claude, Gemini, or LLaMA)")  

    # Parse arguments
    args = parser.parse_args()

    # Interactive user input
    if not args.question:
        console.print("\n[bold yellow]💡 What do you need help with?[/]")
        console.print("[bold white]Example: 'Fix a bug in my script' or 'Generate unit tests for my function'[/]\n")
        args.question = Prompt.ask("[bold cyan]🔎 Enter your request[/]")

    # Model selection with interactive table
    if not args.model:
        console.print("\n[bold yellow]🤖 Choose an AI Model to use:[/]\n")

        model_table = Table(show_header=True, header_style="bold magenta")
        model_table.add_column("Model", style="bold cyan", justify="center")
        model_table.add_column("Description", justify="left")

        model_table.add_row("🦙 LLaMA", "Open-source and efficient AI model")
        model_table.add_row("🔮 Gemini", "Google’s advanced AI for reasoning")
        model_table.add_row("📝 Claude", "Anthropic’s model for structured responses")

        console.print(model_table)
        args.model = Prompt.ask("[bold cyan]🎯 Enter model name (Claude, Gemini, LLaMA)[/]", default="gemini")

    # Display confirmation
    console.print("\n[bold green]🚀 Running GitHub Code Agent...[/]")
    console.print(f"[bold yellow]📌 Request:[/] [bold white]{args.question}[/]")
    console.print(f"[bold yellow]🤖 Model:[/] [bold white]{args.model}[/]\n")

    # Run the agent with provided input
    run_agent(question=args.question, model=args.model, temperature=0)

if __name__ == "__main__":
    main()
