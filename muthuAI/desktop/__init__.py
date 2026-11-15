"""
CHAMP Phase 9C — Real Windows Desktop UI Control & Computer Agent Package.
"""

from desktop.window_manager import WindowManager
from desktop.keyboard_controller import KeyboardController
from desktop.mouse_controller import MouseController
from desktop.ui_inspector import UIInspector
from desktop.screenshot_manager import ScreenshotManager
from desktop.action_verifier import ActionVerifier
from desktop.desktop_controller import DesktopController

__all__ = [
    "WindowManager",
    "KeyboardController",
    "MouseController",
    "UIInspector",
    "ScreenshotManager",
    "ActionVerifier",
    "DesktopController",
]
