"""
MuthuAI — safety/permissions.py
Permission levels for tools and action validation.
"""

from tools.base import PermissionLevel


# Map tool names to their permission level
TOOL_PERMISSIONS: dict[str, PermissionLevel] = {
    # Safe — no confirmation needed
    "open_application": PermissionLevel.SAFE,
    "open_website": PermissionLevel.SAFE,
    "open_folder": PermissionLevel.SAFE,
    "open_file": PermissionLevel.SAFE,
    "volume_up": PermissionLevel.SAFE,
    "volume_down": PermissionLevel.SAFE,
    "mute_volume": PermissionLevel.SAFE,
    "unmute_volume": PermissionLevel.SAFE,
    "take_screenshot": PermissionLevel.SAFE,
    "search_google": PermissionLevel.SAFE,
    "search_youtube": PermissionLevel.SAFE,
    "play_youtube": PermissionLevel.SAFE,
    "web_search": PermissionLevel.SAFE,
    "search_documents": PermissionLevel.SAFE,
    "browser_scroll": PermissionLevel.SAFE,
    "get_system_info": PermissionLevel.SAFE,
    "list_files": PermissionLevel.SAFE,
    "read_file": PermissionLevel.SAFE,
    "stop_media": PermissionLevel.SAFE,
    "pause_media": PermissionLevel.SAFE,

    # Moderate — creates new content, reversible
    "create_excel": PermissionLevel.MODERATE,
    "create_word": PermissionLevel.MODERATE,
    "create_powerpoint": PermissionLevel.MODERATE,
    "create_folder": PermissionLevel.MODERATE,
    "run_command": PermissionLevel.MODERATE,
    "browser_click": PermissionLevel.MODERATE,
    "type_text": PermissionLevel.MODERATE,
    "clipboard_copy": PermissionLevel.MODERATE,

    # Dangerous — requires explicit confirmation
    "delete_file": PermissionLevel.DANGEROUS,
    "delete_folder": PermissionLevel.DANGEROUS,
    "send_message": PermissionLevel.DANGEROUS,
    "submit_form": PermissionLevel.DANGEROUS,
    "change_security_settings": PermissionLevel.DANGEROUS,
    "run_destructive_command": PermissionLevel.DANGEROUS,
}


def get_permission_level(tool_name: str) -> PermissionLevel:
    """Return the permission level for a tool (default: MODERATE if unknown)."""
    return TOOL_PERMISSIONS.get(tool_name, PermissionLevel.MODERATE)
