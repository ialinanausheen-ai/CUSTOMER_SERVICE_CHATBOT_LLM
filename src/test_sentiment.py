from sentiment_engine import analyze_sentiment


test_messages = [
    "I am very happy with your service.",
    "I am extremely frustrated with this terrible service.",
    "Great, another payment problem. Exactly what I needed.",
    "Someone accessed my account without permission.",
    "I was charged twice for the same purchase.",
    "I will take legal action against your company."
]


for message in test_messages:
    result = analyze_sentiment(message)

    print("\nMESSAGE:", message)
    print("SENTIMENT:", result["sentiment"])
    print("CONFIDENCE:", result["confidence"])
    print("TONE:", result["tone"])
    print("FRUSTRATED:", result["frustrated"])
    print("URGENT:", result["urgent"])
    print("SARCASTIC:", result["sarcastic"])
    print("RISK LEVEL:", result["risk_level"])
    print("RISK TYPE:", result["risk_type"])