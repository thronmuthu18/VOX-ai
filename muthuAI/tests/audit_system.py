"""
CHAMP Comprehensive Foundation Audit Script.
Tests all 32 components from Phase 0 / Phase 1 without hanging.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root
sys.path.insert(0, ".")

def main():
    print("==================================================")
    print("      CHAMP FOUNDATION SYSTEM AUDIT SCRIPT        ")
    print("==================================================")

    # 1. Imports check
    modules_to_test = [
        ("1. Entry Point (app.main)", "app.main", "main"),
        ("2. Voice Pipeline", "voice.voice_pipeline", "VoicePipeline"),
        ("3. STT", "voice.stt", "STTProvider"),
        ("4. Wake Word", "voice.wake_word", "WakeWordDetector"),
        ("5. Language Detection", "voice.language_detector", "detect_language"),
        ("6. Gemini Client", "ai.gemini_client", "GeminiClient"),
        ("7. Conversation Manager", "ai.conversation", "ConversationManager"),
        ("8. Agent Orchestrator", "agent.orchestrator", "AgentOrchestrator"),
        ("9. Task Planner", "ai.planner", "AgentPlanner"),
        ("10. Tool Registry", "tools.registry", "ToolRegistry"),
        ("11. Tool Executor", "agent.executor", "TaskExecutor"),
        ("12. Browser Manager", "browser.manager", "BrowserManager"),
        ("13. Windows Controller", "desktop.desktop_controller", "DesktopController"),
        ("14. Keyboard Controller", "desktop.keyboard_controller", "KeyboardController"),
        ("15. Mouse Controller", "desktop.mouse_controller", "MouseController"),
        ("16. Application Tools", "tools.application_tools", "launch_application"),
        ("17. File System Tools", "tools.file_tools", "open_folder"),
        ("18. Office Tools", "tools.office_tools", "create_excel"),
        ("19. WhatsApp Automation", "communication.whatsapp", "WhatsAppService"),
        ("20. Email Automation", "communication.email", None),
        ("21. Instagram Automation", "communication.instagram", "InstagramService"),
        ("22. YouTube Tools", "tools.browser_tools", "play_youtube"),
        ("23. Web Search", "retrieval.web_search", "WebSearcher"),
        ("24. RAG Pipeline", "rag.pipeline", "RAGPipeline"),
        ("25. Personal Memory", "memory.personal_memory", "PersonalMemoryStore"),
        ("26. Current Information", "retrieval.web_search", "is_freshness_query"),
        ("27. PDF Generation", "tools.office_tools", "create_pdf"),
        ("28. n8n Discovery", "n8n.discovery", None),
        ("29. Configuration", "config.settings", "GEMINI_API_KEY"),
        ("30. Environment (.env)", None, None),
        ("31. Tests Suite", "tests", None),
        ("32. Health & Diagnostics", "monitoring.health", "HealthChecker"),
    ]

    print("\n--- 1. Subsystem Import Audit ---")
    audit_results = {}
    for label, mod_path, attr in modules_to_test:
        if mod_path is None:
            # Check file existence for .env
            env_exists = Path(".env").exists()
            status = "OK" if env_exists else "MISSING"
            print(f"  [{status}] {label}")
            audit_results[label] = status
            continue

        try:
            import importlib
            mod = importlib.import_module(mod_path)
            if attr:
                getattr(mod, attr)
            print(f"  [OK] {label}")
            audit_results[label] = "OK"
        except Exception as exc:
            print(f"  [FAIL] {label}: {exc}")
            audit_results[label] = f"FAIL: {exc}"

    # 2. Application resolution check
    print("\n--- 2. Installed Application Resolution Audit ---")
    from tools.application_tools import _find_via_registry, _STANDARD_APP_PATHS, KNOWN_APPS
    apps_to_check = ["chrome", "edge", "vscode", "word", "excel", "powerpoint", "notepad", "calculator", "cmd", "explorer", "settings", "control panel", "whatsapp"]
    for app in apps_to_check:
        reg = _find_via_registry(app)
        std = [p for p in _STANDARD_APP_PATHS.get(app, []) if Path(p).exists()]
        resolved = reg or (std[0] if std else None)
        print(f"  App: {app:15s} -> Registry={bool(reg)} | StandardPath={bool(std)} | Resolved={resolved}")

    # 3. Tool Registry count
    print("\n--- 3. Tool Registry Audit ---")
    from tools import setup_default_registry
    from tools.setup_registry import setup_tools
    from tools.registry import ToolRegistry

    reg1 = setup_default_registry()
    print(f"  setup_default_registry(): {len(reg1)} tools loaded -> {list(reg1.names())[:10]}...")

    reg2 = ToolRegistry()
    setup_tools(reg2)
    print(f"  setup_tools(): {len(reg2)} tools loaded -> {list(reg2.names())[:10]}...")

    # 4. Diagnostics check
    print("\n--- 4. Diagnostics Audit ---")
    from monitoring.health import HealthChecker
    hc = HealthChecker()
    diag = hc.check_all()
    print(f"  HealthChecker healthy: {diag.get('healthy')} | Checks: {diag.get('checks')}")


    print("\n==================================================")
    print("             AUDIT COMPLETE                       ")
    print("==================================================")

if __name__ == "__main__":
    main()
