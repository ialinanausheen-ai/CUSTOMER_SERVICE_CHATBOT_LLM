from sentiment_engine import analyze_sentiment
from conversation_manager import ConversationManager


conversation = ConversationManager()


messages = [
    "Your service is terrible.",
    "I am still waiting for help.",
    "This is really frustrating.",
    "I need someone to fix this."
]


for message in messages:

    result = analyze_sentiment(message)

    conversation.add_message(
        message,
        result
    )


print("\n========== CONVERSATION HISTORY ==========")

for item in conversation.get_history():
    print(item)


print("\n========== NEGATIVE COUNT ==========")
print(conversation.get_negative_count())


print("\n========== CONVERSATION SUMMARY ==========")
print(conversation.get_summary())