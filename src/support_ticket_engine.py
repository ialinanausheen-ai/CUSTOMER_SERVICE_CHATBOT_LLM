import re


def extract_ticket_information(message):
    """
    Extract structured information from a customer message.
    """

    ticket = {
        "customer": None,
        "order_id": None,
        "product": None,
        "issue": None,
        "evidence": None,
        "contact": None
    }

    # Customer name
    customer_match = re.search(
        r"(?:my name is|i am|this is)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)",
        message,
        re.IGNORECASE
    )

    if customer_match:
        ticket["customer"] = customer_match.group(1).strip()

    # Order ID
    order_match = re.search(
        r"(?:my\s+)?order(?:\s*(?:id|number))?\s*(?:is|:|#|-)?\s*([A-Z0-9-]{4,})",
        message,
        re.IGNORECASE
    )

    if order_match:
        ticket["order_id"] = order_match.group(1)

    # Contact information
    email_match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        message
    )

    phone_match = re.search(
        r"(?:\+91[\s-]?)?[6-9]\d{9}",
        message
    )

    if email_match:
        ticket["contact"] = email_match.group(0)

    elif phone_match:
        ticket["contact"] = phone_match.group(0)

           # Product
    product_match = re.search(
        r"(?:product|item)\s*(?:is|:|#|-)?\s*([A-Za-z0-9][A-Za-z0-9 -]{2,40})",
        message,
        re.IGNORECASE
    )

    if not product_match:
        product_match = re.search(
            r"\b(?:ordered|bought|purchased)\s+(.+?)(?=\s+(?:I|my|the|and)\b|[.,]|$)",
            message,
            re.IGNORECASE
        )

    if product_match:
        ticket["product"] = product_match.group(1).strip()
    # Evidence
    evidence_keywords = [
        "screenshot",
        "invoice",
        "receipt",
        "photo",
        "image",
        "proof",
        "document"
    ]

    for keyword in evidence_keywords:
        if keyword in message.lower():
            ticket["evidence"] = keyword
            break

    # Issue
    issue_keywords = [
        "payment",
        "refund",
        "delivery",
        "damaged",
        "missing",
        "wrong item",
        "duplicate charge",
        "account",
        "login",
        "password",
        "order",
        "product"
    ]

    detected_issues = []

    for keyword in issue_keywords:
        if keyword in message.lower():
            detected_issues.append(keyword)

    if detected_issues:
        ticket["issue"] = ", ".join(detected_issues)

    return ticket


def find_missing_information(ticket):
    """
    Identify mandatory information missing from a support ticket.
    """

    mandatory_fields = [
        "customer",
        "order_id",
        "product",
        "issue",
        "contact"
    ]

    missing = []

    for field in mandatory_fields:
        if not ticket.get(field):
            missing.append(field)

    return missing


def calculate_priority(
    sentiment_result,
    issue,
    severity="medium",
    waiting_minutes=0,
    customer_impact="low"
):
    """
    Calculate ticket priority using severity, sentiment,
    waiting time, and customer impact.
    """

    priority_score = 0

    # Severity
    severity_scores = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1
    }

    priority_score += severity_scores.get(severity.lower(), 2)

    # Sentiment
    if sentiment_result.get("sentiment") == "negative":
        priority_score += 2

    if sentiment_result.get("frustrated"):
        priority_score += 1

    if sentiment_result.get("urgent"):
        priority_score += 3

    # High-risk issues
    high_risk_issues = [
        "account",
        "payment",
        "duplicate",
        "legal",
        "security"
    ]

    if issue:
        issue_text = issue.lower()

        for risk in high_risk_issues:
            if risk in issue_text:
                priority_score += 3
                break

    # Waiting time
    if waiting_minutes >= 30:
        priority_score += 3
    elif waiting_minutes >= 15:
        priority_score += 2
    elif waiting_minutes >= 5:
        priority_score += 1

    # Customer impact
    if customer_impact == "high":
        priority_score += 3
    elif customer_impact == "medium":
        priority_score += 2

    # Final priority
    if priority_score >= 10:
        priority = "critical"
    elif priority_score >= 7:
        priority = "high"
    elif priority_score >= 4:
        priority = "medium"
    else:
        priority = "low"

    return {
        "priority": priority,
        "priority_score": priority_score,
        "severity": severity
    }

def calculate_sla(priority, waiting_minutes=0, start_time=None):
    """
    Calculate SLA status using priority, waiting time,
    and optional runtime start time.
    """

    from datetime import datetime

    sla_limits = {
        "critical": 30,
        "high": 60,
        "medium": 120,
        "low": 240
    }

    sla_limit = sla_limits.get(priority, 240)

    # Runtime SLA
    if start_time is not None:
        elapsed_seconds = (
            datetime.now() - start_time
        ).total_seconds()

        runtime_waiting_minutes = elapsed_seconds / 60

        # Use the larger value so simulated testing
        # and actual runtime are both supported.
        waiting_minutes = max(
            waiting_minutes,
            runtime_waiting_minutes
        )

    percentage_used = (waiting_minutes / sla_limit) * 100

    if waiting_minutes >= sla_limit:
        status = "breached"
    elif percentage_used >= 75:
        status = "warning"
    else:
        status = "within_sla"

    return {
        "sla_limit_minutes": sla_limit,
        "waiting_minutes": round(waiting_minutes, 2),
        "percentage_used": round(percentage_used, 2),
        "status": status
    }

def route_ticket(
    issue,
    required_skill,
    agents,
    current_hour=12,
    current_day=None,
    current_date=None
):
    """
    Route a support ticket based on skill, availability,
    workload, weekends, holidays, and business hours.
    """

    # Weekend handling
    if current_day in ["Saturday", "Sunday"]:
        return {
            "status": "weekend",
            "assigned_agent": None,
            "reason": "Support routing is unavailable on weekends."
        }

    # Holiday handling
    holidays = [
        "2026-01-01",
        "2026-01-26",
        "2026-08-15",
        "2026-10-02",
        "2026-12-25"
    ]

    if current_date in holidays:
        return {
            "status": "holiday",
            "assigned_agent": None,
            "reason": "Support routing is unavailable on holidays."
        }

    # Business hours: 9 AM to 6 PM
    if current_hour < 9 or current_hour >= 18:
        return {
            "status": "after_hours",
            "assigned_agent": None,
            "reason": "Support routing is outside business hours."
        }

    matching_agents = []

    for agent in agents:
        if (
            required_skill in agent.get("skills", [])
            and agent.get("available", False)
        ):
            matching_agents.append(agent)

    if not matching_agents:
        return {
            "status": "unavailable",
            "assigned_agent": None,
            "reason": "No available agent with the required skill."
        }

    # Select the available matching agent
    # with the lowest current workload.
    selected_agent = min(
        matching_agents,
        key=lambda agent: agent.get("workload", 0)
    )

    return {
        "status": "assigned",
        "assigned_agent": selected_agent["name"],
        "reason": "Ticket routed to the available agent with the lowest workload."
    }

def classify_issue_relationship(existing_issues, new_issue):
    """
    Determine whether a new issue is a duplicate of an existing issue,
    should be grouped with an existing issue, or should remain separate.
    """

    if not existing_issues:
        return {
            "relationship": "separate",
            "matched_issue": None,
            "reason": "No existing issues found."
        }

    new_issue_text = new_issue.lower()

    for existing_issue in existing_issues:
        existing_text = existing_issue.lower()

        # Exact match
        if new_issue_text == existing_text:
            return {
                "relationship": "duplicate",
                "matched_issue": existing_issue,
                "reason": "The new issue matches an existing issue."
            }

        # Shared important keywords
        new_words = set(new_issue_text.split())
        existing_words = set(existing_text.split())

        common_words = new_words.intersection(existing_words)

        if len(common_words) >= 2:
            return {
                "relationship": "group",
                "matched_issue": existing_issue,
                "reason": "The new issue shares important keywords with an existing issue."
            }

    return {
        "relationship": "separate",
        "matched_issue": None,
        "reason": "The new issue does not match existing issues."
    }


def create_masked_handoff(ticket):
    """
    Create a safe ticket handoff with sensitive contact
    information masked.
    """

    handoff = ticket.copy()

    contact = handoff.get("contact")

    if contact:
        if "@" in contact:
            username, domain = contact.split("@", 1)

            if len(username) > 2:
                masked_username = username[0] + "***" + username[-1]
            else:
                masked_username = "***"

            handoff["contact"] = masked_username + "@" + domain

        else:
            if len(contact) >= 4:
                handoff["contact"] = contact[:2] + "******" + contact[-2:]
            else:
                handoff["contact"] = "***"

    return handoff


def handle_sla_escalation(sla_result):
    """
    Escalate a ticket when its SLA has been breached.
    """

    if sla_result.get("status") == "breached":
        return {
            "escalation_required": True,
            "escalation_level": "high",
            "reason": "Support ticket SLA has been breached."
        }

    elif sla_result.get("status") == "warning":
        return {
            "escalation_required": False,
            "escalation_level": "warning",
            "reason": "Support ticket has reached 75% of its SLA."
        }

    return {
        "escalation_required": False,
        "escalation_level": "none",
        "reason": "Support ticket is within SLA."
    }