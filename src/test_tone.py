from sentiment_engine import analyze_sentiment


test_messages = [
    "I am very happy with your service.",
    "This service is terrible and I am extremely frustrated.",
    "I need this fixed immediately!",
    "Someone accessed my account without permission.",
    "Great, another payment problem. Exactly what I needed.",
    "I need help with my account."
]


for message in test_messages:

    result = analyze_sentiment(message)

    print("\n===================================")
    print("MESSAGE:", message)
    print("SENTIMENT:", result["sentiment"])
    print("FRUSTRATED:", result["frustrated"])
    print("URGENT:", result["urgent"])
    print("SARCASTIC:", result["sarcastic"])
    print("RISK LEVEL:", result["risk_level"])
    print("TONE:", result["tone"])