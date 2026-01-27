"""CLI interface for TokenCrush using Typer."""

import typer
from rich.console import Console
from rich.table import Table

from tokencrush.compressor import TokenCompressor
from tokencrush.providers import LLMProvider
from tokencrush.config import ConfigManager

app = typer.Typer(
    name="tokencrush",
    help="LLM token optimization CLI - compress prompts, save costs.",
)
config_app = typer.Typer(help="Manage API keys and configuration.")
app.add_typer(config_app, name="config")

console = Console()


@app.command()
def compress(
    text: str = typer.Argument(..., help="Text to compress"),
    rate: float = typer.Option(0.5, "--rate", "-r", help="Compression rate (0.0-1.0)"),
    gpu: bool = typer.Option(False, "--gpu", "-g", help="Use GPU for compression"),
):
    """Compress prompt to reduce tokens."""
    with console.status("[bold green]Compressing...[/bold green]"):
        compressor = TokenCompressor(use_gpu=gpu)
        result = compressor.compress(text, rate=rate)
    
    table = Table(title="Compression Result")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Original Tokens", str(result.original_tokens))
    table.add_row("Compressed Tokens", str(result.compressed_tokens))
    table.add_row("Compression Ratio", f"{result.ratio:.1%}")
    table.add_row("Tokens Saved", str(result.original_tokens - result.compressed_tokens))
    
    console.print(table)
    console.print("\n[bold]Compressed Text:[/bold]")
    console.print(result.compressed_text)


@app.command()
def chat(
    prompt: str = typer.Argument(..., help="Prompt to send"),
    model: str = typer.Option("gpt-4", "--model", "-m", help="Model to use"),
    rate: float = typer.Option(0.5, "--rate", "-r", help="Compression rate"),
    gpu: bool = typer.Option(False, "--gpu", "-g", help="Use GPU for compression"),
    no_compress: bool = typer.Option(False, "--no-compress", help="Skip compression"),
):
    """Compress prompt and send to LLM."""
    if not no_compress:
        with console.status("[bold green]Compressing...[/bold green]"):
            compressor = TokenCompressor(use_gpu=gpu)
            result = compressor.compress(prompt, rate=rate)
            compressed_prompt = result.compressed_text
            console.print(f"[dim]Compressed: {result.original_tokens} → {result.compressed_tokens} tokens[/dim]")
    else:
        compressed_prompt = prompt
    
    with console.status(f"[bold blue]Sending to {model}...[/bold blue]"):
        provider = LLMProvider()
        response = provider.chat(compressed_prompt, model=model)
    
    console.print(f"\n[bold]{model}:[/bold]")
    console.print(response)


@config_app.command("set")
def config_set(
    provider: str = typer.Argument(..., help="Provider name (openai, anthropic, google)"),
    key: str = typer.Argument(..., help="API key"),
):
    """Set API key for a provider."""
    config = ConfigManager()
    config.set_api_key(provider, key)
    console.print(f"[green]✓[/green] API key for {provider} saved.")


@config_app.command("show")
def config_show():
    """Show configured API keys."""
    config = ConfigManager()
    providers = config.list_providers()
    
    if not providers:
        console.print("[yellow]No API keys configured.[/yellow]")
        console.print("Use [bold]tokencrush config set <provider> <key>[/bold] to add one.")
        return
    
    table = Table(title="Configured API Keys")
    table.add_column("Provider", style="cyan")
    table.add_column("Key", style="green")
    
    for provider in providers:
        key = config.get_api_key(provider)
        masked = ConfigManager.mask_key(key) if key else "Not set"
        table.add_row(provider, masked)
    
    console.print(table)


if __name__ == "__main__":
    app()
