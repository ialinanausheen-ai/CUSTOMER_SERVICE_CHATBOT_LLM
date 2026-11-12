from support_ticket_engine import (
    extract_ticket_information,
    find_missing_information,
    calculate_priority,
    calculate_sla,
    route_ticket,
    classify_issue_relationship,
    create_masked_handoff,
    handle_sla_escalation
)

from sentiment_engine import analyze_sentiment


message = """
My name is John Smith.
I have a problem with my order.
The product is Wireless Headphones.
Please help me with the delivery.
"""

ticket = extract_ticket_information(message)
missing = find_missing_information(ticket)
sentiment = analyze_sentiment(message)

priority_result = calculate_priority(
    sentiment,
    ticket["issue"],
    waiting_minutes=20,
    customer_impact="high"
)

print("\n===== SUPPORT TICKET =====")
print("Customer:", ticket["customer"])
print("Order ID:", ticket["order_id"])
print("Product:", ticket["product"])
print("Issue:", ticket["issue"])
print("Evidence:", ticket["evidence"])
print("Contact:", ticket["contact"])
print("Missing information:", missing)
print("Priority:", priority_result["priority"])
print("Priority score:", priority_result["priority_score"])
sla_warning = calculate_sla(
    priority_result["priority"],
    waiting_minutes=45
)

sla_breach = calculate_sla(
    priority_result["priority"],
    waiting_minutes=60
)

print("\n===== SLA WARNING TEST =====")
print("SLA limit:", sla_warning["sla_limit_minutes"])
print("Waiting:", sla_warning["waiting_minutes"])
print("SLA used:", sla_warning["percentage_used"], "%")
print("SLA status:", sla_warning["status"])

print("\n===== SLA BREACH TEST =====")
print("SLA limit:", sla_breach["sla_limit_minutes"])
print("Waiting:", sla_breach["waiting_minutes"])
print("SLA used:", sla_breach["percentage_used"], "%")
print("SLA status:", sla_breach["status"])
agents = [
    {
        "name": "Alice",
        "skills": ["payment", "refund"],
        "available": True,
        "workload": 5
    },
    {
        "name": "Bob",
        "skills": ["delivery", "order"],
        "available": True,
        "workload": 2
    },
    {
        "name": "Charlie",
        "skills": ["delivery", "order"],
        "available": False,
        "workload": 1
    }
]

print("\n===== ROUTING TEST =====")

routing_result = route_ticket(
    ticket["issue"],
    required_skill="delivery",
    agents=agents,
    current_hour=12
)

print("Routing status:", routing_result["status"])
print("Assigned agent:", routing_result["assigned_agent"])
print("Reason:", routing_result["reason"])

print("\n===== UNAVAILABLE AGENT TEST =====")

unavailable_result = route_ticket(
    ticket["issue"],
    required_skill="technical",
    agents=agents,
    current_hour=12
)

print("Routing status:", unavailable_result["status"])
print("Assigned agent:", unavailable_result["assigned_agent"])
print("Reason:", unavailable_result["reason"])

print("\n===== AFTER-HOURS TEST =====")

after_hours_result = route_ticket(
    ticket["issue"],
    required_skill="delivery",
    agents=agents,
    current_hour=20
)

print("Routing status:", after_hours_result["status"])
print("Assigned agent:", after_hours_result["assigned_agent"])
print("Reason:", after_hours_result["reason"])
print("\n===== ISSUE RELATIONSHIP TEST =====")

existing_issues = [
    "duplicate payment",
    "delivery delay"
]

duplicate_result = classify_issue_relationship(
    existing_issues,
    "duplicate payment"
)

group_result = classify_issue_relationship(
    existing_issues,
    "delivery delay for my order"
)

separate_result = classify_issue_relationship(
    existing_issues,
    "password reset"
)

print("\nDuplicate test:")
print("Relationship:", duplicate_result["relationship"])
print("Matched issue:", duplicate_result["matched_issue"])
print("Reason:", duplicate_result["reason"])

print("\nGroup test:")
print("Relationship:", group_result["relationship"])
print("Matched issue:", group_result["matched_issue"])
print("Reason:", group_result["reason"])

print("\nSeparate test:")
print("Relationship:", separate_result["relationship"])
print("Matched issue:", separate_result["matched_issue"])
print("Reason:", separate_result["reason"])
print("\n===== MASKED HANDOFF TEST =====")

complete_message = """
My name is John Smith.
My order is ORD12345.
The product is Wireless Headphones.
I was charged twice for the same payment.
I have a screenshot as proof.
You can contact me at john@example.com.
"""

complete_ticket = extract_ticket_information(complete_message)

masked_handoff = create_masked_handoff(complete_ticket)

print("Original contact:", complete_ticket["contact"])
print("Masked contact:", masked_handoff["contact"])
print("Original ticket:", complete_ticket)
print("Masked handoff:", masked_handoff)
print("\n===== SLA ESCALATION TEST =====")

warning_escalation = handle_sla_escalation(sla_warning)
breach_escalation = handle_sla_escalation(sla_breach)

print("\n75% SLA warning:")
print("Escalation required:", warning_escalation["escalation_required"])
print("Escalation level:", warning_escalation["escalation_level"])
print("Reason:", warning_escalation["reason"])

print("\nSLA breach:")
print("Escalation required:", breach_escalation["escalation_required"])
print("Escalation level:", breach_escalation["escalation_level"])
print("Reason:", breach_escalation["reason"])