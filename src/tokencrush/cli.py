"""CLI interface for TokenCrush using Typer."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from tokencrush.compressor import TokenCompressor
from tokencrush.config import ConfigManager
from tokencrush.sdk import TokenCrush

app = typer.Typer(
    name="tokencrush",
    help="LLM token optimization CLI - compress prompts, save costs.",
)
config_app = typer.Typer(help="Manage API keys and configuration.")
cache_app = typer.Typer(help="Manage cache and view cache statistics.")
app.add_typer(config_app, name="config")
app.add_typer(cache_app, name="cache")

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
    table.add_row(
        "Tokens Saved", str(result.original_tokens - result.compressed_tokens)
    )

    console.print(table)
    console.print("\n[bold]Compressed Text:[/bold]")
    console.print(result.compressed_text)


@app.command()
def chat(
    prompt: str = typer.Argument(..., help="Prompt to send"),
    model: str = typer.Option(
        "gpt-4", "--model", "-m", help="Model to use (for paid API fallback)"
    ),
    rate: float = typer.Option(0.5, "--rate", "-r", help="Compression rate"),
    gpu: bool = typer.Option(False, "--gpu", "-g", help="Use GPU for compression"),
    no_compress: bool = typer.Option(False, "--no-compress", help="Skip compression"),
    smart: bool = typer.Option(True, "--smart", help="Use smart routing (default)"),
    local: bool = typer.Option(False, "--local", help="Force local LLM only"),
    free_api: bool = typer.Option(False, "--free-api", help="Force free API only"),
):
    """Compress prompt and send to LLM using smart routing."""
    if local:
        mode = "local"
    elif free_api:
        mode = "free"
    else:
        mode = "smart"

    tc = TokenCrush(compression_rate=rate)

    with console.status(f"[bold blue]Routing via {mode}...[/bold blue]"):
        response = tc.chat(prompt, mode=mode)

    console.print(f"\n[bold green]{response}[/bold green]")

    stats = tc.stats()
    console.print(
        Panel(
            (
                f"[dim]Mode: {mode} | Cache hit rate: {stats.cache_hit_rate:.1%} | "
                f"Total queries: {stats.total_queries}[/dim]"
            ),
            title="[cyan]Routing Info[/cyan]",
        )
    )


@config_app.command("set")
def config_set(
    provider: str = typer.Argument(
        ..., help="Provider name (openai, anthropic, google)"
    ),
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
        console.print(
            "Use [bold]tokencrush config set <provider> <key>[/bold] to add one."
        )
        return

    table = Table(title="Configured API Keys")
    table.add_column("Provider", style="cyan")
    table.add_column("Key", style="green")

    for provider in providers:
        key = config.get_api_key(provider)
        masked = ConfigManager.mask_key(key) if key else "Not set"
        table.add_row(provider, masked)

    console.print(table)


@app.command()
def stats():
    """Show cache statistics and cost savings."""
    tc = TokenCrush()
    sdk_stats = tc.stats()

    table = Table(title="TokenCrush Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Cache Hit Rate", f"{sdk_stats.cache_hit_rate:.1%}")
    table.add_row("Total Queries", str(sdk_stats.total_queries))
    table.add_row("Cache Hits", str(sdk_stats.cached))
    table.add_row("Cost Saved", f"${sdk_stats.cost_saved:.2f}")

    console.print(table)


@cache_app.command("clear")
def cache_clear():
    """Clear all cache entries."""
    tc = TokenCrush()
    tc.router.cache.clear()
    console.print("[green]✓[/green] Cache cleared successfully.")


@cache_app.command("stats")
def cache_stats():
    """Show cache statistics."""
    tc = TokenCrush()
    sdk_stats = tc.stats()

    table = Table(title="Cache Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Hit Rate", f"{sdk_stats.cache_hit_rate:.1%}")
    table.add_row("Total Queries", str(sdk_stats.total_queries))
    table.add_row("Cache Hits", str(sdk_stats.cached))
    table.add_row("Cache Misses", str(sdk_stats.total_queries - sdk_stats.cached))

    console.print(table)


@app.command()
def serve(
    port: int = typer.Option(8080, "--port", "-p", help="Port to bind to"),
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
):
    """Start OpenAI-compatible proxy server with caching and compression."""
    import uvicorn

    console.print(f"[green]Starting TokenCrush proxy on {host}:{port}[/green]")
    console.print("[dim]Endpoints:[/dim]")
    console.print(f"  [cyan]POST[/cyan] http://{host}:{port}/v1/chat/completions")
    console.print(f"  [cyan]GET[/cyan]  http://{host}:{port}/v1/models")
    console.print(f"  [cyan]GET[/cyan]  http://{host}:{port}/health")

    uvicorn.run("tokencrush.proxy:app", host=host, port=port, log_level="info")


@app.command()
def install():
    """Install TokenCrush system-wide for all AI tools."""
    from tokencrush import daemon
    from tokencrush import shell_config

    console.print("[bold]Installing TokenCrush...[/bold]\n")

    with console.status("Starting proxy daemon..."):
        if daemon.start():
            console.print("[green]✓[/green] Proxy daemon started on port 8765")
        else:
            console.print("[red]✗[/red] Failed to start daemon")
            raise typer.Exit(1)

    with console.status("Configuring shell profiles..."):
        profiles = shell_config.install_to_all_profiles()
        for p in profiles:
            console.print(f"[green]✓[/green] Configured {p}")

    console.print("\n[bold green]Installation complete![/bold green]\n")
    console.print("TokenCrush is now active for:")
    console.print("  • Cursor")
    console.print("  • Claude Code")
    console.print("  • OpenCode")
    console.print("  • Any OpenAI-compatible tool")
    console.print("\n[dim]Restart your terminal or run: source ~/.zshrc[/dim]")


@app.command()
def uninstall():
    """Uninstall TokenCrush system-wide configuration."""
    from tokencrush import daemon
    from tokencrush import shell_config

    console.print("[bold]Uninstalling TokenCrush...[/bold]\n")

    with console.status("Stopping proxy daemon..."):
        daemon.stop()
        console.print("[green]✓[/green] Proxy daemon stopped")

    with console.status("Removing shell configuration..."):
        profiles = shell_config.uninstall_from_all_profiles()
        for p in profiles:
            console.print(f"[green]✓[/green] Cleaned {p}")

    console.print("\n[bold green]Uninstallation complete![/bold green]")
    console.print("[dim]Restart your terminal to apply changes.[/dim]")


@app.command("daemon-status")
def daemon_status():
    """Show TokenCrush daemon status."""
    from tokencrush import daemon as daemon_module

    info = daemon_module.status()

    table = Table(title="TokenCrush Daemon Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Daemon Running", "Yes" if info["running"] else "No")
    table.add_row("PID", str(info["pid"]) if info["pid"] else "-")
    table.add_row("Port", str(info["port"]))
    table.add_row("Proxy URL", info["url"])

    console.print(table)


if __name__ == "__main__":
    app()
