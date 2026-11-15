"""
CHAMP Test for multi-step task execution.
"""

import sys
sys.path.insert(0, ".")

from ai.gemini_client import GeminiClient
from ai.conversation import ConversationManager
from ai.planner import AgentPlanner
from tools import setup_default_registry
from safety.validator import ActionValidator
from safety.confirmation import ConfirmationHandler
from agent.orchestrator import AgentOrchestrator

def main():
    gemini_client = GeminiClient()
    conversation = ConversationManager()
    registry = setup_default_registry()
    planner = AgentPlanner(gemini_client, registry)
    validator = ActionValidator()
    confirmation = ConfirmationHandler()

    orch = AgentOrchestrator(
        gemini_client=gemini_client,
        conversation=conversation,
        planner=planner,
        registry=registry,
        validator=validator,
        confirmation=confirmation,
    )

    print("=== TEST 1: Open Chrome and open YouTube ===")
    res1 = orch.process_turn("Bro, open Chrome and open YouTube.", wake_authenticated=True)
    print("Response 1:", res1)

    print("\n=== TEST 2: Office Excel creation ===")
    res2 = orch.process_turn("Bro, create an Excel sheet with Name, Age and Mark.", wake_authenticated=True)
    print("Response 2:", res2)

    print("\n=== TEST 3: Office Word creation ===")
    res3 = orch.process_turn("Bro, create a Word document about Machine Learning.", wake_authenticated=True)
    print("Response 3:", res3)

    print("\n=== TEST 4: Office PDF generation ===")
    res4 = orch.process_turn("Bro, create a PDF report about Artificial Intelligence.", wake_authenticated=True)
    print("Response 4:", res4)

    print("\n=== TEST 5: System Volume ===")
    res5 = orch.process_turn("Bro, increase volume.", wake_authenticated=True)
    print("Response 5:", res5)

    print("\n=== TEST 6: Calculator ===")
    res6 = orch.process_turn("Bro, open Calculator.", wake_authenticated=True)
    print("Response 6:", res6)

    print("\n=== TEST 7: Current News (Web Search) ===")
    res7 = orch.process_turn("Bro, what is the latest AI news?", wake_authenticated=True)
    print("Response 7:", res7)

    print("\n=== TEST 8: Conversational Question (Negative test - No Tools) ===")
    res8 = orch.process_turn("Bro, what is machine learning?", wake_authenticated=True)
    print("Response 8:", res8)

if __name__ == "__main__":
    main()
