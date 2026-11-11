from sentiment_engine import analyze_sentiment


test_messages = [
    "Hola, necesito ayuda con mi cuenta.",
    "Bonjour, j'ai un problème avec mon paiement.",
    "नमस्ते, मुझे अपने खाते में समस्या है।",
    "வணக்கம், எனது கணக்கில் பிரச்சனை உள்ளது.",
    "سلام، مجھے اپنے اکاؤنٹ میں مدد چاہیے."
]


for message in test_messages:

    result = analyze_sentiment(message)

    print("\n===================================")
    print("MESSAGE:", message)
    print("LANGUAGE:", result["language"])
    print("SENTIMENT:", result["sentiment"])
    print("CONFIDENCE:", result["confidence"])
    print("TONE:", result["tone"])
    print("RISK LEVEL:", result["risk_level"])
    print("RISK TYPE:", result["risk_type"])