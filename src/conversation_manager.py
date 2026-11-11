class ConversationManager:

    def __init__(self):
        self.history = []

    def add_message(self, message, sentiment_result):
        self.history.append({
            "message": message,
            "sentiment": sentiment_result.get("sentiment"),
            "confidence": sentiment_result.get("confidence"),
            "tone": sentiment_result.get("tone"),
            "frustrated": sentiment_result.get("frustrated"),
            "urgent": sentiment_result.get("urgent"),
            "sarcastic": sentiment_result.get("sarcastic"),
            "risk_level": sentiment_result.get("risk_level"),
            "risk_type": sentiment_result.get("risk_type")
        })

    def get_history(self):
        return self.history

    def get_negative_count(self):
        return sum(
            1
            for item in self.history
            if item.get("sentiment") == "negative"
        )

    def get_summary(self):
        if not self.history:
            return "No conversation history."

        total_messages = len(self.history)

        negative_messages = sum(
            1 for item in self.history
            if item.get("sentiment") == "negative"
        )

        urgent_messages = sum(
            1 for item in self.history
            if item.get("urgent")
        )

        high_risk_messages = sum(
            1 for item in self.history
            if item.get("risk_level") == "high"
        )

        frustrated_messages = sum(
            1 for item in self.history
            if item.get("frustrated")
        )

        return {
            "total_messages": total_messages,
            "negative_messages": negative_messages,
            "urgent_messages": urgent_messages,
            "frustrated_messages": frustrated_messages,
            "high_risk_messages": high_risk_messages,
            "latest_message": self.history[-1]["message"],
            "latest_sentiment": self.history[-1]["sentiment"],
            "latest_tone": self.history[-1]["tone"]
        }