"""
CHAMP Phase 3 — browser/discovery.py

Robust browser executable discovery on Windows.
Never assumes chrome.exe or msedge.exe is available in PATH.
Uses Windows Registry (HKLM, HKCU App Paths) and standard installation directories.
"""

from __future__ import annotations
import os
import shutil
import getpass
from pathlib import Path
from utils.logger import get_logger

log = get_logger("muthuai.browser.discovery")

_USERNAME = getpass.getuser()

# Standard Windows installation paths
_CHROME_STANDARD_PATHS: list[str] = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    rf"C:\Users\{_USERNAME}\AppData\Local\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
]

_EDGE_STANDARD_PATHS: list[str] = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    rf"C:\Users\{_USERNAME}\AppData\Local\Microsoft\Edge\Application\msedge.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"),
]

_BRAVE_STANDARD_PATHS: list[str] = [
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    rf"C:\Users\{_USERNAME}\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe",
]


def find_via_registry(app_name: str) -> str | None:
    """
    Look up application executable path from Windows Registry App Paths.
    Checks both HKLM and HKCU for '<app_name>.exe' and '<app_name>'.
    """
    try:
        import winreg
        sub_keys = [
            rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{app_name}.exe",
            rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{app_name}",
        ]
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for sk in sub_keys:
                try:
                    with winreg.OpenKey(root, sk) as key:
                        val, _ = winreg.QueryValueEx(key, "")
                        if val:
                            p = Path(val.strip('"'))
                            if p.exists():
                                log.info("Found %s in Windows Registry: %s", app_name, p)
                                return str(p)
                except (FileNotFoundError, OSError):
                    pass
    except Exception as exc:
        log.debug("Registry lookup error for %s: %s", app_name, exc)
    return None


def find_chrome_executable() -> str | None:
    """
    Find installed Google Chrome executable on Windows.
    Order:
      1. Windows Registry (HKLM / HKCU App Paths)
      2. Standard Program Files / LocalAppData paths
      3. PATH (shutil.which)
    """
    # 1. Registry
    reg = find_via_registry("chrome")
    if reg:
        return reg

    # 2. Standard paths
    for path_str in _CHROME_STANDARD_PATHS:
        p = Path(path_str)
        if p.exists() and p.is_file():
            log.info("Found Chrome at standard path: %s", p)
            return str(p)

    # 3. PATH fallback
    w = shutil.which("chrome") or shutil.which("chrome.exe")
    if w and Path(w).exists():
        log.info("Found Chrome in PATH: %s", w)
        return w

    log.warning("Google Chrome executable could not be located on this system.")
    return None


def find_edge_executable() -> str | None:
    """
    Find installed Microsoft Edge executable on Windows.
    """
    # 1. Registry
    reg = find_via_registry("msedge") or find_via_registry("edge")
    if reg:
        return reg

    # 2. Standard paths
    for path_str in _EDGE_STANDARD_PATHS:
        p = Path(path_str)
        if p.exists() and p.is_file():
            log.info("Found Edge at standard path: %s", p)
            return str(p)

    # 3. PATH fallback
    w = shutil.which("msedge") or shutil.which("msedge.exe") or shutil.which("edge")
    if w and Path(w).exists():
        log.info("Found Edge in PATH: %s", w)
        return w

    log.warning("Microsoft Edge executable could not be located on this system.")
    return None


def find_brave_executable() -> str | None:
    """Find Brave browser if installed."""
    reg = find_via_registry("brave")
    if reg:
        return reg
    for path_str in _BRAVE_STANDARD_PATHS:
        p = Path(path_str)
        if p.exists():
            return str(p)
    return shutil.which("brave") or shutil.which("brave.exe")


def get_browser_executable(browser_type: str = "chrome") -> str | None:
    """
    Get the path to the executable for the requested browser.
    Accepts: 'chrome', 'google chrome', 'edge', 'msedge', 'microsoft edge', 'brave'.
    """
    b = browser_type.lower().strip()
    if "chrome" in b:
        return find_chrome_executable()
    elif "edge" in b:
        return find_edge_executable()
    elif "brave" in b:
        return find_brave_executable()
    return find_chrome_executable() or find_edge_executable()


def get_available_browsers() -> dict[str, str]:
    """Return a dictionary of installed browser names and executable paths."""
    browsers = {}
    chrome = find_chrome_executable()
    if chrome:
        browsers["chrome"] = chrome
    edge = find_edge_executable()
    if edge:
        browsers["edge"] = edge
    brave = find_brave_executable()
    if brave:
        browsers["brave"] = brave
    return browsers
