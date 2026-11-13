import streamlit as st
import time
from datetime import datetime

from langchain_helper import get_qa_chain, create_vector_db
from sentiment_engine import analyze_sentiment
from conversation_manager import ConversationManager
from escalation_engine import evaluate_escalation
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
from knowledge_base_pipeline import (
    detect_prompt_injection,
    mask_sensitive_data,
    record_monitoring_metrics,
    run_health_check,
    automatic_rollback
)



st.title("CUSTOMER SERVICE CHATBOT 🤖")


# Create conversation manager
if "conversation_manager" not in st.session_state:
    st.session_state["conversation_manager"] = ConversationManager()

conversation_manager = st.session_state["conversation_manager"]


# Create Knowledgebase
btn = st.button("Create Knowledgebase")

if btn:
    create_vector_db()
    st.success("Knowledgebase created successfully.")


# Customer question
with st.form("chat_form"):
    question = st.text_input("Question: ")
    waiting_minutes = st.number_input(
        "Simulated waiting time (minutes)",
        min_value=0,
        value=0
    )
    send_message = st.form_submit_button("Send")

if send_message and question:
        # Task 3: Prompt-injection protection
    injection_check = detect_prompt_injection(question)

    if not injection_check["safe"]:
        st.error(
            "⚠️ Potential prompt injection detected. "
            "This request was blocked for security."
        )
        st.write(f"Detected patterns: {injection_check['patterns']}")
        st.stop()
    

    # 1. Analyze sentiment
    sentiment = analyze_sentiment(
        question,
        conversation_manager.get_history()
    )

    # 2. Get current hour
    current_hour = datetime.now().hour

    # Simulated time control for testing
    use_simulated_time = st.checkbox(
        "Use simulated time for testing"
    )

    if use_simulated_time:
        simulated_hour = st.number_input(
            "Simulated hour (0-23)",
            min_value=0,
            max_value=23,
            value=current_hour
        )
        current_hour = simulated_hour

    # 3. Evaluate escalation using previous conversation history
    escalation = evaluate_escalation(
        question,
        sentiment,
        conversation_manager.get_history(),
        current_hour=current_hour
    )

    # 4. Add current message to conversation history
    conversation_manager.add_message(
        question,
        sentiment
    )

    # 5. Display customer sentiment
    st.subheader("Customer Sentiment")

    st.write(f"Sentiment: {sentiment['sentiment']}")
    st.write(f"Tone: {sentiment['tone']}")
    st.write(f"Confidence: {sentiment['confidence']}")
    st.write(f"Frustrated: {sentiment['frustrated']}")
    st.write(f"Urgent: {sentiment['urgent']}")
    st.write(f"Sarcastic: {sentiment['sarcastic']}")
    st.write(f"Risk Level: {sentiment['risk_level']}")

    if sentiment["risk_type"]:
        st.write(f"Risk Type: {sentiment['risk_type']}")

    # 6. Display escalation information
    st.subheader("Escalation")

    st.write(
        f"Escalation Required: "
        f"{escalation['escalation_required']}"
    )

    st.write(
        f"Escalation Level: "
        f"{escalation['escalation_level']}"
    )

    st.write(
        f"Escalation Reason: "
        f"{escalation['escalation_reason']}"
    )

    st.write(
        f"Activated Conditions: "
        f"{escalation['activated_conditions']}"
    )

    st.write(
        f"Handling Action: "
        f"{escalation['handling_action']}"
    )

    # 7. Human escalation warning
    if escalation["escalation_required"]:
        st.warning(
            "⚠️ This conversation requires human support. "
            "Please escalate this customer to a support agent."
        )

                    # 8. Create structured support ticket
    masked_ticket_question = mask_sensitive_data(question)
    ticket = extract_ticket_information(masked_ticket_question)
    missing_information = find_missing_information(ticket)

    priority = calculate_priority(
        sentiment,
        ticket["issue"],
        severity="medium",
        waiting_minutes=waiting_minutes,
        customer_impact="medium"
    )

    if "ticket_start_time" not in st.session_state:
        st.session_state["ticket_start_time"] = datetime.now()

    ticket_sla = calculate_sla(
        priority["priority"],
        waiting_minutes=waiting_minutes,
        start_time=st.session_state["ticket_start_time"]
    )

    # Display support ticket
    st.subheader("Support Ticket")

    st.write(f"Customer: {ticket['customer']}")
    st.write(f"Order ID: {ticket['order_id']}")
    st.write(f"Product: {ticket['product']}")
    st.write(f"Issue: {ticket['issue']}")
    st.write(f"Evidence: {ticket['evidence']}")
    st.write(f"Contact: {ticket['contact']}")

    if missing_information:
        st.warning(
            f"Missing mandatory information: {missing_information}"
        )
    else:
        st.success("All mandatory ticket information is available.")

    st.write(
        f"Priority: {priority['priority']}"
    )

    st.write(
        f"Priority Score: {priority['priority_score']}"
    )

    st.write(
        f"SLA Status: {ticket_sla['status']}"
    )

    st.write(
        f"SLA Limit: {ticket_sla['sla_limit_minutes']} minutes"
    )

    # Support agents
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

    # Route ticket
    required_skill = "order"

    if ticket["issue"]:
        issue_text = ticket["issue"].lower()

        if "payment" in issue_text or "duplicate" in issue_text:
            required_skill = "payment"

        elif "refund" in issue_text:
            required_skill = "refund"

        elif "delivery" in issue_text:
            required_skill = "delivery"

        elif "order" in issue_text:
            required_skill = "order"

    routing = route_ticket(
    ticket["issue"],
    required_skill,
    agents,
    current_hour=current_hour,
    current_day=datetime.now().strftime("%A"),
    current_date=datetime.now().strftime("%Y-%m-%d")
)

    st.write(f"Routing Status: {routing['status']}")
    st.write(f"Assigned Agent: {routing['assigned_agent']}")
    st.write(f"Routing Reason: {routing['reason']}")
    # SLA escalation
    sla_escalation = handle_sla_escalation(ticket_sla)

    if sla_escalation["escalation_required"]:
        st.error(
            f"SLA Escalation: {sla_escalation['reason']}"
        )
    elif sla_escalation["escalation_level"] == "warning":
        st.warning(
            f"SLA Warning: {sla_escalation['reason']}"
        )
            # Task 3: Mask sensitive data before LLM processing
    masked_question = mask_sensitive_data(question)

    # 8. Generate chatbot response
    st.header("Answer")
    response_start_time = time.time()
    response_failure_count = 0

    try:
        chain = get_qa_chain()
        response = chain.invoke({"query": masked_question})
        response_latency_ms = round(
            (time.time() - response_start_time) * 1000,
            2
        )

        monitoring_metrics = record_monitoring_metrics(
            latency_ms=response_latency_ms,
            failure_count=response_failure_count,
            confidence_score=sentiment["confidence"],
            escalation_count=1 if escalation["escalation_required"] else 0
        )

        st.subheader("Task 3 Monitoring")
        st.write(f"Response Latency: {monitoring_metrics['latency_ms']} ms")
        st.write(f"Failures: {monitoring_metrics['failure_count']}")
        st.write(
            f"Confidence: {monitoring_metrics['confidence_score']}"
        )
        st.write(
            f"Escalations: {monitoring_metrics['escalation_count']}"
        )

       
        st.write(response["result"])
        

    except Exception as e:
        response_failure_count = 1
        error_message = str(e)

        if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            st.warning(
                "The chatbot's AI response service is temporarily unavailable "
                "because the API request quota has been reached. "
                "The sentiment and escalation analysis is still available."
            )
        else:
            st.error(
                "The chatbot response could not be generated at this time."
            )

    # 9. Conversation summary
    st.subheader("Conversation Summary")
    st.write(escalation["conversation_summary"])