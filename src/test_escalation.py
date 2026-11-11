from sentiment_engine import analyze_sentiment
from escalation_engine import evaluate_escalation


test_cases = [
    {
        "message": "I need this fixed immediately!",
        "current_hour": 20
    },
    {
        "message": "I need help with my account.",
        "current_hour": 20
    },
    {
        "message": "This is terrible. I am still waiting.",
        "current_hour": 12,
        "minutes_unresolved": 20
    }
]


for test in test_cases:

    message = test["message"]

    sentiment_result = analyze_sentiment(message)

    escalation_result = evaluate_escalation(
        message=message,
        sentiment_result=sentiment_result,
        minutes_unresolved=test.get("minutes_unresolved", 0),
        current_hour=test["current_hour"]
    )

    print("\n===================================")
    print("MESSAGE:", message)
    print("CURRENT HOUR:", test["current_hour"])
    print("SENTIMENT:", sentiment_result["sentiment"])
    print("URGENT:", sentiment_result["urgent"])
    print("ESCALATION REQUIRED:",
          escalation_result["escalation_required"])
    print("ESCALATION LEVEL:",
          escalation_result["escalation_level"])
    print("ESCALATION REASON:",
          escalation_result["escalation_reason"])
    print("ACTIVATED CONDITIONS:",
          escalation_result["activated_conditions"])
    print("HANDLING ACTION:",
          escalation_result["handling_action"])