"""Shell profile configuration for TokenCrush."""

from pathlib import Path
from typing import List

MARKER_START = "# >>> tokencrush >>>"
MARKER_END = "# <<< tokencrush <<<"

ENV_BLOCK = """# >>> tokencrush >>>
# TokenCrush: Auto-configured LLM proxy
export OPENAI_API_BASE="http://127.0.0.1:8765/v1"
export OPENAI_BASE_URL="http://127.0.0.1:8765/v1"
# <<< tokencrush <<<"""


def get_shell_profiles() -> List[Path]:
    """Get list of shell profile files to configure."""
    home = Path.home()
    candidates = [
        home / ".zshrc",
        home / ".bashrc",
        home / ".bash_profile",
        home / ".config" / "fish" / "config.fish",
    ]
    return [p for p in candidates if p.exists()]


def is_configured(profile: Path) -> bool:
    """Check if profile already has TokenCrush config."""
    content = profile.read_text()
    return MARKER_START in content


def add_to_profile(profile: Path) -> bool:
    """Add TokenCrush env vars to shell profile."""
    if is_configured(profile):
        return True

    content = profile.read_text()
    content += f"\n\n{ENV_BLOCK}\n"
    profile.write_text(content)
    return True


def remove_from_profile(profile: Path) -> bool:
    """Remove TokenCrush config from shell profile."""
    if not is_configured(profile):
        return True

    content = profile.read_text()
    lines = content.split("\n")
    new_lines = []
    skip = False

    for line in lines:
        if MARKER_START in line:
            skip = True
            continue
        if MARKER_END in line:
            skip = False
            continue
        if not skip:
            new_lines.append(line)

    profile.write_text("\n".join(new_lines))
    return True


def install_to_all_profiles() -> List[Path]:
    """Install to all detected shell profiles."""
    modified = []
    for profile in get_shell_profiles():
        if add_to_profile(profile):
            modified.append(profile)
    return modified


def uninstall_from_all_profiles() -> List[Path]:
    """Remove from all shell profiles."""
    modified = []
    for profile in get_shell_profiles():
        if remove_from_profile(profile):
            modified.append(profile)
    return modified
