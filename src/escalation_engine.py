def evaluate_escalation(
    message,
    sentiment_result,
    conversation_history=None,
    minutes_unresolved=0,
    current_hour=12
):
    """
    Evaluates whether a customer conversation requires escalation.
    """

    reasons = []
    activated_conditions = []

    # 1. HIGH-RISK ISSUES
    risk_type = sentiment_result.get("risk_type")

    if risk_type == "account_compromise":
        reasons.append("Possible account compromise detected")
        activated_conditions.append("account_compromise")

    elif risk_type == "duplicate_payment":
        reasons.append("Duplicate payment detected")
        activated_conditions.append("duplicate_payment")

    elif risk_type == "legal_threat":
        reasons.append("Legal threat detected")
        activated_conditions.append("legal_threat")

    # 2. REPEATED NEGATIVE MESSAGES
    negative_count = 0

    if conversation_history:
        for item in conversation_history:
            if item.get("sentiment") == "negative":
                negative_count += 1

    if sentiment_result.get("sentiment") == "negative":
        negative_count += 1

    if negative_count >= 3:
        reasons.append("Repeated negative sentiment detected")
        activated_conditions.append("repeated_negative")

    # 3. NEGATIVE ISSUE UNRESOLVED >15 MIN
    if (
        sentiment_result.get("sentiment") == "negative"
        and minutes_unresolved > 15
    ):
        reasons.append(
            "Negative issue unresolved for more than 15 minutes"
        )
        activated_conditions.append("negative_unresolved_15min")

    # 4. AFTER-HOURS HANDLING
    urgent = sentiment_result.get("urgent", False)
    after_hours = current_hour < 9 or current_hour >= 18

    handling_action = "normal"

    if urgent and after_hours:
        reasons.append("Urgent issue received after business hours")
        activated_conditions.append("urgent_after_hours")
        handling_action = "on_call"

    elif after_hours and not urgent:
        reasons.append("Non-urgent issue received after business hours")
        activated_conditions.append("normal_after_hours")
        handling_action = "next_working_day"

    # 5. CONVERSATION SUMMARY
    total_messages = len(conversation_history) if conversation_history else 0

    negative_messages = 0
    urgent_messages = 0
    frustrated_messages = 0
    high_risk_messages = 0

    if conversation_history:
        for item in conversation_history:
            if item.get("sentiment") == "negative":
                negative_messages += 1

            if item.get("urgent"):
                urgent_messages += 1

            if item.get("frustrated"):
                frustrated_messages += 1

            if item.get("risk_level") == "high":
                high_risk_messages += 1

    if sentiment_result.get("sentiment") == "negative":
        negative_messages += 1

    if sentiment_result.get("urgent"):
        urgent_messages += 1

    if sentiment_result.get("frustrated"):
        frustrated_messages += 1

    if sentiment_result.get("risk_level") == "high":
        high_risk_messages += 1

    conversation_summary = {
        "total_messages": total_messages + 1,
        "negative_messages": negative_messages,
        "urgent_messages": urgent_messages,
        "frustrated_messages": frustrated_messages,
        "high_risk_messages": high_risk_messages,
        "latest_message": message,
        "latest_sentiment": sentiment_result.get("sentiment"),
        "latest_tone": sentiment_result.get("tone")
    }

    # 6. ESCALATION STATUS
    escalation_required = len(reasons) > 0

    if escalation_required:
        escalation_level = "high"
    else:
        escalation_level = "none"

    return {
        "escalation_required": escalation_required,
        "escalation_level": escalation_level,
        "escalation_reason": reasons,
        "activated_conditions": activated_conditions,
        "handling_action": handling_action,
        "conversation_summary": conversation_summary
    }