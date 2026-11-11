import re
from textblob import TextBlob


def detect_language(message):
    """
    Detect the language of the current message.
    """

    language_patterns = {
        "Spanish": [
            "hola",
            "gracias",
            "ayuda",
            "problema",
            "por favor",
            "necesito",
            "pago",
            "cuenta",
            "cobro"
        ],

        "French": [
            "bonjour",
            "merci",
            "aide",
            "problème",
            "s'il vous plaît",
            "paiement",
            "compte",
            "heureux",
            "génial"
        ],

        "German": [
            "hallo",
            "danke",
            "hilfe",
            "bitte",
            "brauche",
            "zahlung",
            "konto",
            "großartig",
            "ausgezeichnet"
        ],

        "Hindi": [
            "नमस्ते",
            "धन्यवाद",
            "मदद",
            "समस्या",
            "सेवा",
            "चाहिए",
            "कृपया",
            "भुगतान",
            "खाता"
        ],

        "Tamil": [
            "வணக்கம்",
            "நன்றி",
            "உதவி",
            "பிரச்சனை",
            "சேவை",
            "வேண்டும்",
            "தயவு",
            "பணம்",
            "கணக்கு"
        ],

        "Urdu": [
            "سلام",
            "شکریہ",
            "مدد",
            "مسئلہ",
            "سروس",
            "چاہیے",
            "براہ کرم",
            "ادائیگی",
            "اکاؤنٹ"
        ]
    }

    message_lower = message.lower()

    for language, patterns in language_patterns.items():
        if any(pattern in message_lower for pattern in patterns):
            return language

    return "English"


def analyze_sentiment(message, conversation_history=None):
    """
    Analyze the customer's current message.

    Returns:
        sentiment
        confidence
        tone
        frustrated
        urgent
        sarcastic
        risk_level
        risk_type
        language
    """

    if conversation_history is None:
        conversation_history = []

    # Handle conversation history containing strings or dictionaries
    history_text_parts = []

    for item in conversation_history:
        if isinstance(item, dict):
            history_text_parts.append(
                str(item.get("message", ""))
            )
        else:
            history_text_parts.append(str(item))

    history_text = " ".join(history_text_parts)

    current_text = message.lower()

    combined_text = f"{history_text} {message}".strip()
    text = combined_text.lower()

    language = detect_language(message)

    # --------------------------------------------------
    # MULTILINGUAL ANALYSIS
    # --------------------------------------------------

    if language != "English":

        multilingual_patterns = {
            "Spanish": {
                "negative": [
                    "problema",
                    "terrible",
                    "horrible",
                    "malo",
                    "mal",
                    "frustrado",
                    "frustrante"
                ],
                "positive": [
                    "excelente",
                    "genial",
                    "gracias",
                    "feliz",
                    "bueno"
                ],
                "urgent": [
                    "urgente",
                    "inmediatamente",
                    "ahora mismo",
                    "lo antes posible"
                ]
            },

            "French": {
                "negative": [
                    "problème",
                    "terrible",
                    "horrible",
                    "mauvais",
                    "frustré",
                    "frustrant"
                ],
                "positive": [
                    "excellent",
                    "génial",
                    "merci",
                    "heureux",
                    "bon"
                ],
                "urgent": [
                    "urgent",
                    "immédiatement",
                    "maintenant",
                    "dès que possible"
                ]
            },

            "German": {
                "negative": [
                    "problem",
                    "schrecklich",
                    "schlecht",
                    "frustriert",
                    "frustrierend"
                ],
                "positive": [
                    "ausgezeichnet",
                    "großartig",
                    "danke",
                    "glücklich",
                    "gut"
                ],
                "urgent": [
                    "dringend",
                    "sofort",
                    "jetzt",
                    "so schnell wie möglich"
                ]
            },

            "Hindi": {
                "negative": [
                    "समस्या",
                    "खराब",
                    "बहुत बुरा",
                    "परेशान",
                    "निराश"
                ],
                "positive": [
                    "बहुत अच्छा",
                    "शानदार",
                    "धन्यवाद",
                    "खुश",
                    "अच्छा"
                ],
                "urgent": [
                    "तुरंत",
                    "जरूरी",
                    "अभी",
                    "जल्दी"
                ]
            },

            "Tamil": {
                "negative": [
                    "பிரச்சனை",
                    "மோசம்",
                    "மோசமான",
                    "விரக்தி",
                    "வருத்தம்"
                ],
                "positive": [
                    "சிறந்தது",
                    "அருமை",
                    "நன்றி",
                    "மகிழ்ச்சி",
                    "நல்லது"
                ],
                "urgent": [
                    "அவசரம்",
                    "உடனடியாக",
                    "இப்போதே",
                    "விரைவாக"
                ]
            },

            "Urdu": {
                "negative": [
                    "مسئلہ",
                    "خراب",
                    "بہت برا",
                    "پریشان",
                    "مایوس"
                ],
                "positive": [
                    "بہترین",
                    "زبردست",
                    "شکریہ",
                    "خوش",
                    "اچھا"
                ],
                "urgent": [
                    "فوری",
                    "فوراً",
                    "ابھی",
                    "جلدی"
                ]
            }
        }

        patterns = multilingual_patterns.get(language, {})

        negative_match = any(
            phrase in current_text
            for phrase in patterns.get("negative", [])
        )

        positive_match = any(
            phrase in current_text
            for phrase in patterns.get("positive", [])
        )

        urgent = any(
            phrase in current_text
            for phrase in patterns.get("urgent", [])
        )

        if negative_match:
            sentiment = "negative"
            confidence = 0.8
        elif positive_match:
            sentiment = "positive"
            confidence = 0.8
        else:
            sentiment = "neutral"
            confidence = 0.0

        # --------------------------------------------------
        # MULTILINGUAL FRUSTRATION
        # --------------------------------------------------

        frustration_patterns = {
            "Spanish": [
                "frustrado",
                "frustrante",
                "enojado",
                "molesto"
            ],

            "French": [
                "frustré",
                "frustrant",
                "énervé",
                "mécontent"
            ],

            "German": [
                "frustriert",
                "frustrierend",
                "verärgert",
                "enttäuscht"
            ],

            "Hindi": [
                "परेशान",
                "निराश",
                "गुस्सा",
                "झुंझलाहट"
            ],

            "Tamil": [
                "விரக்தி",
                "எரிச்சல்",
                "கோபம்",
                "வருத்தம்"
            ],

            "Urdu": [
                "پریشان",
                "مایوس",
                "غصہ",
                "جھنجھلاہٹ"
            ]
        }

        frustrated = any(
            phrase in current_text
            for phrase in frustration_patterns.get(language, [])
        )

        # --------------------------------------------------
        # MULTILINGUAL SARCASM
        # --------------------------------------------------

        sarcasm_patterns = {
            "Spanish": [
                "gracias por nada",
                "qué sorpresa",
                "genial, otro"
            ],

            "French": [
                "merci pour rien",
                "quelle surprise",
                "super, encore"
            ],

            "German": [
                "danke für nichts",
                "was für eine überraschung",
                "toll, noch eine"
            ],

            "Hindi": [
                "वाह, क्या बात है",
                "धन्यवाद कुछ नहीं के लिए"
            ],

            "Tamil": [
                "நன்றி எதற்கும் இல்லை",
                "என்ன ஒரு ஆச்சரியம்"
            ],

            "Urdu": [
                "شکریہ کسی چیز کے لیے نہیں",
                "کیا حیرت ہے"
            ]
        }

        sarcastic = any(
            phrase in current_text
            for phrase in sarcasm_patterns.get(language, [])
        )

        # Sarcastic messages are treated as negative
        if sarcastic:
            sentiment = "negative"
            confidence = max(confidence, 0.6)

        # --------------------------------------------------
        # MULTILINGUAL RISK PHRASES
        # --------------------------------------------------

        risk_type = None
        risk_level = "low"

        risk_patterns = {
            "account_compromise": [
                "cuenta hackeada",
                "acceso no autorizado",
                "compte piraté",
                "accès non autorisé",
                "konto gehackt",
                "unbefugter zugriff",
                "खाता हैक",
                "अनधिकृत पहुंच",
                "கணக்கு ஹேக்",
                "அனுமதியற்ற அணுகல்",
                "اکاؤنٹ ہیک",
                "غیر مجاز رسائی"
            ],

            "duplicate_payment": [
                "cobrado dos veces",
                "paiement en double",
                "zweimal belastet",
                "दो बार भुगतान",
                "இரண்டு முறை கட்டணம்",
                "دو بار ادائیگی"
            ],

            "legal_threat": [
                "acción legal",
                "action en justice",
                "rechtliche Schritte",
                "कानूनी कार्रवाई",
                "சட்ட நடவடிக்கை",
                "قانونی کارروائی"
            ]
        }

        for risk, phrases in risk_patterns.items():
            if any(phrase in current_text for phrase in phrases):
                risk_type = risk
                risk_level = "high"
                break

        # --------------------------------------------------
        # MULTILINGUAL RESPONSE TONE
        # --------------------------------------------------

        if risk_level == "high":
            tone = "calm_and_reassuring"

        elif frustrated or sentiment == "negative":
            tone = "empathetic"

        elif urgent:
            tone = "urgent_and_helpful"

        elif sentiment == "positive":
            tone = "friendly"

        else:
            tone = "professional"

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "tone": tone,
            "frustrated": frustrated,
            "urgent": urgent,
            "sarcastic": sarcastic,
            "risk_level": risk_level,
            "risk_type": risk_type,
            "language": language
        }

    # --------------------------------------------------
    # ENGLISH SENTIMENT
    # --------------------------------------------------

    polarity = TextBlob(combined_text).sentiment.polarity

    if polarity > 0.2:
        sentiment = "positive"
    elif polarity < -0.2:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    confidence = round(min(abs(polarity), 1.0), 2)

    # --------------------------------------------------
    # FRUSTRATION
    # --------------------------------------------------

    frustration_words = [
        "angry",
        "frustrated",
        "frustrating",
        "annoyed",
        "annoying",
        "disappointed",
        "terrible",
        "horrible",
        "awful",
        "worst",
        "unacceptable",
        "ridiculous",
        "useless",
        "fed up",
        "sick of",
        "waste of time",
        "bad service"
    ]

    frustrated = any(
        phrase in current_text
        for phrase in frustration_words
    )

    # --------------------------------------------------
    # URGENCY
    # --------------------------------------------------

    urgency_words = [
        "urgent",
        "urgently",
        "asap",
        "immediately",
        "right now",
        "emergency",
        "critical",
        "today",
        "as soon as possible"
    ]

    urgent = any(
        phrase in current_text
        for phrase in urgency_words
    )

    # --------------------------------------------------
    # SARCASM
    # --------------------------------------------------

    sarcasm_patterns = [
        "great, another",
        "just what i needed",
        "exactly what i needed",
        "thanks for nothing",
        "what a surprise",
        "love being",
        "wonderful, another",
        "perfect, another",
        "oh great",
        "yeah, great",
        "amazing, another"
    ]

    sarcasm_marker = any(
        phrase in current_text
        for phrase in sarcasm_patterns
    )

    quoted_negative_words = re.findall(
        r'"([^"]+)"',
        current_text
    )

    sarcastic = (
        sarcasm_marker
        or len(quoted_negative_words) > 0
    )

    # Sarcastic complaints are treated as negative
    if sarcastic:
        sentiment = "negative"
        confidence = max(confidence, 0.6)

    # Explicit positive customer expressions
    positive_words = [
        "happy",
        "excellent",
        "amazing",
        "great service",
        "love your service",
        "very good",
        "wonderful",
        "satisfied",
        "thank you"
    ]

    # Explicit sarcasm detection
    if any(phrase in current_text for phrase in sarcasm_patterns):
        sarcastic = True
        sentiment = "negative"
        confidence = max(confidence, 0.6)

    elif any(phrase in current_text for phrase in positive_words):
        sentiment = "positive"
        confidence = max(confidence, 0.8)

    # --------------------------------------------------
    # HIGH-RISK ISSUES
    # --------------------------------------------------

    risk_type = None
    risk_level = "low"

    account_compromise = [
        "someone accessed my account",
        "someone hacked my account",
        "account hacked",
        "account compromised",
        "unauthorized access",
        "unauthorised access",
        "someone logged into my account",
        "unknown login"
    ]

    duplicate_payment = [
        "duplicate payment",
        "charged twice",
        "charged two times",
        "double charged",
        "duplicate charge",
        "paid twice"
    ]

    legal_threat = [
        "lawyer",
        "legal action",
        "sue you",
        "sue your company",
        "court",
        "legal complaint",
        "consumer court",
        "report you legally"
    ]

    if any(phrase in current_text for phrase in account_compromise):
        risk_type = "account_compromise"
        risk_level = "high"

    elif any(phrase in current_text for phrase in duplicate_payment):
        risk_type = "duplicate_payment"
        risk_level = "high"

    elif any(phrase in current_text for phrase in legal_threat):
        risk_type = "legal_threat"
        risk_level = "high"

    # --------------------------------------------------
    # RESPONSE TONE
    # --------------------------------------------------

    if risk_level == "high":
        tone = "calm_and_reassuring"

    elif sarcastic or frustrated or sentiment == "negative":
        tone = "empathetic"

    elif urgent:
        tone = "urgent_and_helpful"

    elif sentiment == "positive":
        tone = "friendly"

    else:
        tone = "professional"

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "tone": tone,
        "frustrated": frustrated,
        "urgent": urgent,
        "sarcastic": sarcastic,
        "risk_level": risk_level,
        "risk_type": risk_type,
        "language": language
    }