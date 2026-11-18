from datetime import datetime, timedelta
import re


class ConversationManager:

    # Task 6 configurable settings
    MAX_CONTEXT_MESSAGES = 10
    SESSION_TIMEOUT_MINUTES = 30
    SUMMARY_RESTORE_HOURS = 24

    LANGUAGE_CONFIDENCE_THRESHOLD = 0.60
    INTENT_CONFIDENCE_THRESHOLD = 0.60

    SUPPORTED_LANGUAGES = [
        "English",
        "Spanish",
        "French",
        "German",
        "Hindi",
        "Tamil",
        "Urdu"
    ]

    def __init__(self):
        self.sessions = {}
        self.active_session_id = "default"
        self._create_session(self.active_session_id)

    def _create_session(self, session_id):
        self.sessions[session_id] = {
            "history": [],
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "summary": None,
            "active": True
        }

    def _get_session(self, session_id=None):
        session_id = session_id or self.active_session_id

        if session_id not in self.sessions:
            self._create_session(session_id)

        return self.sessions[session_id]

    def _check_session_expiry(self, session_id=None):
        session = self._get_session(session_id)
        now = datetime.now()

        inactivity = now - session["last_activity"]

        if inactivity > timedelta(
            minutes=self.SESSION_TIMEOUT_MINUTES
        ):
            self._save_summary(session_id)
            session["active"] = False

        return session

    def start_session(self, session_id="default"):
        """
        Start or restore a customer session.

        If the previous session expired within 24 hours,
        restore its conversation summary.

        Otherwise start a completely new session.
        """

        now = datetime.now()

        if session_id not in self.sessions:
            self._create_session(session_id)
            self.active_session_id = session_id

            return {
                "status": "new",
                "summary": None
            }

        session = self.sessions[session_id]

        if session["active"]:
            self.active_session_id = session_id

            return {
                "status": "active",
                "summary": session["summary"]
            }

        if session["summary"] is not None:
            summary_age = now - session["last_activity"]

            if summary_age <= timedelta(
                hours=self.SUMMARY_RESTORE_HOURS
            ):
                old_summary = session["summary"]

                self._create_session(session_id)

                self.sessions[session_id]["summary"] = old_summary
                self.active_session_id = session_id

                return {
                    "status": "restored",
                    "summary": old_summary
                }

        self._create_session(session_id)
        self.active_session_id = session_id

        return {
            "status": "new",
            "summary": None
        }

    def detect_multiple_requests(self, message):
        """
        Detect multiple customer requests in a single message.

        Correction messages such as:
        "My order is ORD123. Sorry, I meant ORD456."
        are treated as one request.
        """

        correction = self.detect_correction(message)

        if correction["correction_detected"]:
            return {
                "multiple_requests": False,
                "request_count": 1,
                "requests": [message.strip()]
            }

        separators = re.split(
            r'\s+(?:and|also|but|plus|as well as)\s+|[.!?]\s+|,\s+(?=(?:I|i)\s)',
            message,
            flags=re.IGNORECASE
        )

        requests = [
            part.strip()
            for part in separators
            if part.strip()
        ]

        meaningful_requests = [
            part
            for part in requests
            if len(part.split()) >= 3
        ]

        return {
            "multiple_requests": len(meaningful_requests) > 1,
            "request_count": len(meaningful_requests),
            "requests": meaningful_requests
        }

    def detect_correction(self, message):
        """
        Detect whether the customer is correcting previously
        provided information.
        """

        correction_patterns = [
            r"\bi meant\b",
            r"\bactually\b",
            r"\bsorry,?\s+i meant\b",
            r"\bcorrection\b",
            r"\bcorrect (?:order|id|number|amount|date)\b",
            r"\bthe correct\b",
            r"\bplease correct\b",
            r"\bnot .* but\b"
        ]

        message_lower = message.lower()

        detected = any(
            re.search(pattern, message_lower)
            for pattern in correction_patterns
        )

        return {
            "correction_detected": detected,
            "message": message
        }

    def check_clarification_needed(
        self,
        language_confidence,
        intent_confidence=None
    ):
        """
        Check whether clarification is needed because
        language or intent confidence is low.
        """

        language_threshold = self.LANGUAGE_CONFIDENCE_THRESHOLD
        intent_threshold = self.INTENT_CONFIDENCE_THRESHOLD

        if language_confidence < language_threshold:
            return {
                "clarification_needed": True,
                "reason": "Low language confidence"
            }

        if (
            intent_confidence is not None
            and intent_confidence < intent_threshold
        ):
            return {
                "clarification_needed": True,
                "reason": "Low intent confidence"
            }

        return {
            "clarification_needed": False,
            "reason": None
        }

    def extract_order_id(self, message):
        """
        Extract an order ID from a customer message.

        Returns the LAST order ID found so corrected
        information can replace previously provided information.
        """

        matches = re.findall(
            r'\b(?:ORD|ORDER)[-_]?[A-Z0-9]*\d[A-Z0-9]*\b',
            message,
            re.IGNORECASE
        )

        if matches:
            return matches[-1].upper()

        return None

    def extract_date(self, message):
        """
        Extract common date formats from a customer message.
        """

        date_patterns = [
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b"
        ]

        for pattern in date_patterns:
            match = re.search(
                pattern,
                message,
                re.IGNORECASE
            )

            if match:
                return match.group(0)

        return None

    def add_message(
        self,
        message,
        sentiment_result,
        session_id=None,
        metadata=None
    ):
        session = self._check_session_expiry(session_id)

        if not session["active"]:
            session_id = session_id or self.active_session_id
            self.start_session(session_id)
            session = self._get_session(session_id)

        entry = {
            "message": message,
            "sentiment": sentiment_result.get("sentiment"),
            "confidence": sentiment_result.get("confidence"),
            "tone": sentiment_result.get("tone"),
            "frustrated": sentiment_result.get("frustrated"),
            "urgent": sentiment_result.get("urgent"),
            "sarcastic": sentiment_result.get("sarcastic"),
            "risk_level": sentiment_result.get("risk_level"),
            "risk_type": sentiment_result.get("risk_type"),
            "language": sentiment_result.get("language"),
            "timestamp": datetime.now().isoformat()
        }

        if metadata:
            entry["metadata"] = metadata

        # Task 6: corrected information detection
        correction = self.detect_correction(message)

        entry["correction_detected"] = (
            correction["correction_detected"]
        )

        # Task 6: preserve latest order ID
        order_id = self.extract_order_id(message)

        if order_id:
            entry["order_id"] = order_id

        # Task 6: preserve date information
        date_value = self.extract_date(message)

        if date_value:
            entry["date"] = date_value

        session["history"].append(entry)

        # Keep at least the configured context window
        if len(session["history"]) > self.MAX_CONTEXT_MESSAGES:
            session["history"] = session["history"][
                -self.MAX_CONTEXT_MESSAGES:
            ]

        session["last_activity"] = datetime.now()
        session["active"] = True

    def get_history(self, session_id=None):
        session = self._check_session_expiry(session_id)

        return session["history"][
            -self.MAX_CONTEXT_MESSAGES:
        ]

    def get_full_history(self, session_id=None):
        session = self._get_session(session_id)
        return session["history"]

    def get_negative_count(self, session_id=None):
        return sum(
            1
            for item in self.get_history(session_id)
            if item.get("sentiment") == "negative"
        )

    def get_latest_order_id(self, session_id=None):
        """
        Return the most recently provided order ID.
        """

        history = self.get_history(session_id)

        for item in reversed(history):
            if item.get("order_id"):
                return item["order_id"]

        return None

    def get_summary(self, session_id=None):
        session = self._get_session(session_id)

        history = session["history"]

        if not history:
            return "No conversation history."

        total_messages = len(history)

        negative_messages = sum(
            1
            for item in history
            if item.get("sentiment") == "negative"
        )

        urgent_messages = sum(
            1
            for item in history
            if item.get("urgent")
        )

        high_risk_messages = sum(
            1
            for item in history
            if item.get("risk_level") == "high"
        )

        frustrated_messages = sum(
            1
            for item in history
            if item.get("frustrated")
        )

        languages = list({
            item.get("language")
            for item in history
            if item.get("language")
        })

        return {
            "total_messages": total_messages,
            "negative_messages": negative_messages,
            "urgent_messages": urgent_messages,
            "frustrated_messages": frustrated_messages,
            "high_risk_messages": high_risk_messages,
            "languages": languages,
            "latest_message": history[-1]["message"],
            "latest_sentiment": history[-1]["sentiment"],
            "latest_tone": history[-1]["tone"]
        }

    def _save_summary(self, session_id=None):
        session = self._get_session(session_id)

        history = session["history"]

        if not history:
            session["summary"] = None
            return

        session["summary"] = {
            "total_messages": len(history),
            "latest_message": history[-1]["message"],
            "latest_sentiment": history[-1]["sentiment"],
            "latest_language": history[-1].get("language"),
            "languages": list({
                item.get("language")
                for item in history
                if item.get("language")
            }),
            "last_updated": datetime.now().isoformat()
        }

    def get_session_status(self, session_id=None):
        session = self._check_session_expiry(session_id)

        return {
            "session_id": session_id or self.active_session_id,
            "active": session["active"],
            "message_count": len(session["history"]),
            "last_activity": session["last_activity"].isoformat(),
            "summary_available": session["summary"] is not None
        }

    def end_session(self, session_id=None):
        session = self._get_session(session_id)

        self._save_summary(session_id)

        session["active"] = False

    def set_active_session(self, session_id):
        if session_id not in self.sessions:
            self._create_session(session_id)

        self.active_session_id = session_id