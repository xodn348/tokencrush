"""Command-line interface for TokenCrush."""

import typer

app = typer.Typer()


@app.command()
def compress(prompt: str) -> None:
    """Compress a prompt to reduce token count."""
    typer.echo(f"Compressing prompt: {prompt}")


if __name__ == "__main__":
    app()
