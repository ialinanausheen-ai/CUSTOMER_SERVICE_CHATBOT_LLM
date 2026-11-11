from sentiment_engine import analyze_sentiment
from conversation_manager import ConversationManager
from escalation_engine import evaluate_escalation


conversation = ConversationManager()


messages = [
    "Your service is terrible.",
    "I am still waiting and this is frustrating.",
    "This is really bad. Nobody is helping me."
]


for message in messages:

    sentiment_result = analyze_sentiment(message)

    conversation.add_message(
        message,
        sentiment_result
    )


last_message = messages[-1]

last_sentiment = analyze_sentiment(last_message)


escalation_result = evaluate_escalation(
    message=last_message,
    sentiment_result=last_sentiment,
    conversation_history=conversation.get_history()
)


print("\n========== REPEATED NEGATIVE TEST ==========")

print("Negative message count:",
      conversation.get_negative_count())

print("Escalation required:",
      escalation_result["escalation_required"])

print("Escalation level:",
      escalation_result["escalation_level"])

print("Escalation reason:",
      escalation_result["escalation_reason"])

print("Activated conditions:",
      escalation_result["activated_conditions"])