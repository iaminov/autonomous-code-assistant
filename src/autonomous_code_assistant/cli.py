"""Modern CLI interface for the autonomous code assistant."""

import os
import sys
from pathlib import Path
from typing import Any

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm

from .core import CodeAssistant
from .exceptions import CodeAssistantError


# Load environment variables
load_dotenv()

console = Console()


@click.group()
@click.option(
    "--provider", 
    default="openai", 
    help="LLM provider to use (default: openai)"
)
@click.option(
    "--model", 
    default=None, 
    help="Model name to use (provider-specific)"
)
@click.option(
    "--project-root", 
    default=".", 
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Project root directory"
)
@click.option(
    "--verbose", 
    "-v", 
    is_flag=True, 
    help="Enable verbose output"
)
@click.pass_context
def main(ctx: click.Context, provider: str, model: str | None, project_root: str, verbose: bool) -> None:
    """Autonomous Code Assistant - AI-powered coding companion."""
    
    ctx.ensure_object(dict)
    
    # Initialize the assistant
    try:
        kwargs = {}
        if model:
            kwargs["model"] = model
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task(description="Initializing assistant...", total=None)
            assistant = CodeAssistant(
                provider_name=provider,
                project_root=project_root,
                **kwargs
            )
        
        ctx.obj["assistant"] = assistant
        ctx.obj["verbose"] = verbose
        
        if verbose:
            provider_info = assistant.get_provider_info()
            console.print(f"[green]✓[/green] Initialized with {provider_info['name']} ({provider_info['model']})")
            
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to initialize assistant: {str(e)}")
        raise click.Abort()


@main.command()
@click.argument("instruction")
@click.option(
    "--file", 
    "-f", 
    type=click.Path(),
    help="Target file to modify"
)
@click.option(
    "--max-tokens", 
    default=4096, 
    help="Maximum tokens for generation"
)
@click.option(
    "--temperature", 
    default=0.2, 
    type=float,
    help="Generation temperature (0.0-2.0)"
)
@click.option(
    "--no-backup", 
    is_flag=True, 
    help="Skip creating backup when modifying files"
)
@click.option(
    "--dry-run", 
    is_flag=True, 
    help="Show what would be generated without applying changes"
)
@click.pass_context
def generate(
    ctx: click.Context, 
    instruction: str, 
    file: str | None, 
    max_tokens: int, 
    temperature: float,
    no_backup: bool,
    dry_run: bool
) -> None:
    """Generate code based on an instruction."""
    
    assistant: CodeAssistant = ctx.obj["assistant"]
    verbose = ctx.obj["verbose"]
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(description="Generating code...", total=None)
            
            result = assistant.process_instruction(
                instruction=instruction,
                target_file=file if not dry_run else None,
                max_tokens=max_tokens,
                temperature=temperature,
                create_backup=not no_backup
            )
        
        # Display results
        console.print(Panel(
            instruction,
            title="[bold blue]Instruction[/bold blue]",
            expand=False
        ))
        
        if file:
            # Detect language for syntax highlighting
            language = assistant.code_analyzer.detect_language(file, result["generated_content"])
            
            syntax = Syntax(
                result["generated_content"],
                language or "text",
                theme="monokai",
                line_numbers=True
            )
            
            console.print(Panel(
                syntax,
                title=f"[bold green]Generated Code[/bold green] ({language or 'unknown'})",
                expand=False
            ))
        else:
            console.print(Panel(
                result["generated_content"],
                title="[bold green]Generated Content[/bold green]",
                expand=False
            ))
        
        # Show metadata
        if verbose:
            table = Table(title="Generation Metadata")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="magenta")
            
            table.add_row("Model", result["model"])
            table.add_row("Tokens Used", str(result["tokens_used"]))
            table.add_row("Finish Reason", result["finish_reason"])
            
            if result.get("backup_created"):
                table.add_row("Backup Created", "Yes")
                table.add_row("Backup Path", result.get("backup_path", ""))
            
            console.print(table)
        
        if dry_run:
            console.print("[yellow]Note: This was a dry run. No files were modified.[/yellow]")
        elif file and result.get("file_modified"):
            console.print(f"[green]✓[/green] Successfully modified {file}")
            
    except CodeAssistantError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()


@main.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.pass_context
def review(ctx: click.Context, filepath: str) -> None:
    """Review code in a file and provide suggestions."""
    
    assistant: CodeAssistant = ctx.obj["assistant"]
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task(description="Reviewing code...", total=None)
            result = assistant.review_code(filepath)
        
        console.print(Panel(
            f"File: {filepath} ({result['language'] or 'unknown'})",
            title="[bold blue]Code Review[/bold blue]",
            expand=False
        ))
        
        console.print(Panel(
            result["review"],
            title="[bold yellow]Review Results[/bold yellow]",
            expand=False
        ))
        
    except CodeAssistantError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()


@main.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.argument("refactor_instruction")
@click.option(
    "--no-backup", 
    is_flag=True, 
    help="Skip creating backup when modifying files"
)
@click.pass_context
def refactor(ctx: click.Context, filepath: str, refactor_instruction: str, no_backup: bool) -> None:
    """Refactor code in a file based on instructions."""
    
    assistant: CodeAssistant = ctx.obj["assistant"]
    
    if not Confirm.ask(f"This will modify {filepath}. Continue?", default=True):
        console.print("[yellow]Refactoring cancelled.[/yellow]")
        return
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task(description="Refactoring code...", total=None)
            result = assistant.refactor_code(filepath, refactor_instruction)
        
        console.print(f"[green]✓[/green] Successfully refactored {filepath}")
        
        if result.get("backup_created"):
            console.print(f"[blue]ℹ[/blue] Backup created: {result.get('backup_path')}")
            
    except CodeAssistantError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()


@main.command()
@click.option(
    "--include", 
    multiple=True, 
    help="Glob patterns to include (can be used multiple times)"
)
@click.pass_context
def analyze(ctx: click.Context, include: tuple[str, ...]) -> None:
    """Analyze the project structure and dependencies."""
    
    assistant: CodeAssistant = ctx.obj["assistant"]
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task(description="Analyzing project...", total=None)
            result = assistant.analyze_project(list(include) if include else None)
        
        # Project overview
        overview_table = Table(title="Project Overview")
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="magenta")
        
        overview_table.add_row("Project Root", result["project_root"])
        overview_table.add_row("Total Files", str(result["total_files"]))
        overview_table.add_row("Total Lines", str(result["total_lines"]))
        overview_table.add_row("Languages Found", str(len(result["languages"])))
        overview_table.add_row("Dependencies Found", str(len(result["dependencies"])))
        
        console.print(overview_table)
        
        # Languages breakdown
        if result["languages"]:
            lang_table = Table(title="Languages")
            lang_table.add_column("Language", style="cyan")
            lang_table.add_column("Files", style="magenta")
            
            for lang, count in sorted(result["languages"].items()):
                lang_table.add_row(lang, str(count))
            
            console.print(lang_table)
        
        # Dependencies
        if result["dependencies"]:
            deps_list = "\n".join(f"• {dep}" for dep in result["dependencies"][:20])
            if len(result["dependencies"]) > 20:
                deps_list += f"\n... and {len(result['dependencies']) - 20} more"
            
            console.print(Panel(
                deps_list,
                title="[bold green]Dependencies[/bold green]",
                expand=False
            ))
        
        # Errors
        if result["errors"]:
            console.print(f"[yellow]⚠[/yellow] {len(result['errors'])} files had analysis errors")
            
    except CodeAssistantError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()


@main.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.pass_context
def document(ctx: click.Context, filepath: str) -> None:
    """Generate documentation for code in a file."""
    
    assistant: CodeAssistant = ctx.obj["assistant"]
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task(description="Generating documentation...", total=None)
            result = assistant.generate_documentation(filepath)
        
        console.print(Panel(
            f"File: {filepath} ({result['language'] or 'unknown'})",
            title="[bold blue]Documentation Generation[/bold blue]",
            expand=False
        ))
        
        console.print(Panel(
            result["documentation"],
            title="[bold green]Generated Documentation[/bold green]",
            expand=False
        ))
        
    except CodeAssistantError as e:
        console.print(f"[red]✗[/red] {str(e)}")
        raise click.Abort()


@main.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show information about the current provider and assistant."""
    
    assistant: CodeAssistant = ctx.obj["assistant"]
    
    try:
        provider_info = assistant.get_provider_info()
        
        table = Table(title="Assistant Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Provider", provider_info["name"])
        table.add_row("Model", provider_info["model"])
        table.add_row("Health Check", "✓ Healthy" if provider_info["health_check"] else "✗ Unhealthy")
        
        capabilities = ", ".join(provider_info["capabilities"])
        table.add_row("Capabilities", capabilities)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to get provider info: {str(e)}")
        raise click.Abort()


if __name__ == "__main__":
    main()
