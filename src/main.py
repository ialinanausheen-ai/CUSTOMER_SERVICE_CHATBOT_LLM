import streamlit as st
import time
from datetime import datetime
from dotenv import load_dotenv

from langchain_helper import (
    get_qa_chain,
    create_vector_db,
    answer_question
)

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

from multimodal_evidence_engine import process_uploaded_file


st.title("CUSTOMER SERVICE CHATBOT 🤖")


# Task 6: Customer session management
if "customer_session_id" not in st.session_state:
    st.session_state["customer_session_id"] = "customer_default"

customer_session_id = st.text_input(
    "Customer Session ID",
    value=st.session_state["customer_session_id"]
)

st.session_state["customer_session_id"] = (
    customer_session_id.strip() or "customer_default"
)

if "conversation_manager" not in st.session_state:
    st.session_state["conversation_manager"] = ConversationManager()

conversation_manager = st.session_state["conversation_manager"]

if conversation_manager.active_session_id != st.session_state["customer_session_id"]:
    conversation_manager.start_session(
        st.session_state["customer_session_id"]
    )


# Create Knowledgebase
btn = st.button("Create Knowledgebase")

if btn:
    create_vector_db()
    st.success("Knowledgebase created successfully.")

st.subheader("Knowledge Access")

customer_access_level = st.selectbox(
    "Customer access level",
    ["public", "customer", "agent", "admin"],
    index=1
)

historical_question = st.checkbox(
    "Historical question"
)

historical_date = None

if historical_question:
    historical_date = st.date_input(
        "Policy date",
        value=datetime.now().date()
    ).isoformat()


# Task 5: Multimodal evidence upload
st.subheader("Evidence Upload")

uploaded_file = st.file_uploader(
    "Upload a screenshot, invoice, PDF, or product image",
    type=["png", "jpg", "jpeg", "webp", "pdf"],
    max_upload_size=10
)

evidence_message = st.text_area(
    "Message related to the uploaded evidence",
    placeholder="Example: My order ID is ORD12345 and I was charged Rs 2499."
)

if uploaded_file is not None:

    if st.button("Process Uploaded Evidence"):

        file_bytes = uploaded_file.getvalue()

        evidence_result = process_uploaded_file(
            uploaded_file.name,
            file_bytes,
            evidence_message
        )

        if evidence_result["status"] == "processed":

            st.success(
                evidence_result["reason"]
            )

            st.write(
                "Evidence:",
                evidence_result["evidence"]
            )

            if evidence_result["comparison"]["match"]:
                st.success(
                    "Evidence matches the customer's message."
                )
            else:
                st.warning(
                    "Evidence conflicts with the customer's message."
                )

        elif evidence_result["status"] == "conflict_detected":

            st.warning(
                evidence_result["reason"]
            )

            st.write(
                "Conflicts:",
                evidence_result["comparison"]["conflicts"]
            )

        elif evidence_result["status"] == "clarification_required":

            st.warning(
                evidence_result["reason"]
            )

        elif evidence_result["status"] == "queued":

            st.info(
                "Your evidence is taking longer than 30 seconds "
                "to process and has been moved to the background queue."
            )

            st.write(
                "Job ID:",
                evidence_result["job"]["job_id"]
            )

        elif evidence_result["status"] == "rejected":

            st.error(
                evidence_result["reason"]
            )


# Customer question
with st.form("chat_form"):
    question = st.text_input("Question: ")

    waiting_minutes = st.number_input(
        "Simulated waiting time (minutes)",
        min_value=0,
        value=0
    )

    send_message = st.form_submit_button("Send")


# Task 6: Local ambiguous follow-up detector
# This keeps main.py working even if the ConversationManager
# currently does not contain this method.
def detect_ambiguous_follow_up(message):
    import re

    ambiguous_patterns = [
        r"\bthat one\b",
        r"\bthis one\b",
        r"\bthe other one\b",
        r"\bthe previous one\b",
        r"\bthe earlier one\b",
        r"\bwhat about that\b",
        r"\bwhat about this\b",
        r"\bwhat about it\b",
        r"\bhow about that\b",
        r"\bhow about this\b",
        r"\bwhich one\b"
    ]

    message_lower = message.lower().strip()

    detected = any(
        re.search(pattern, message_lower)
        for pattern in ambiguous_patterns
    )

    return {
        "ambiguous_follow_up": detected,
        "message": message
    }


if send_message and question:

    # Task 3: Prompt-injection protection
    injection_check = detect_prompt_injection(question)

    if not injection_check["safe"]:
        st.error(
            "⚠️ Potential prompt injection detected. "
            "This request was blocked for security."
        )

        st.write(
            f"Detected patterns: {injection_check['patterns']}"
        )

        st.stop()


    # 1. Analyze sentiment
    sentiment = analyze_sentiment(
        question,
        conversation_manager.get_history()
    )


    # Task 6: Request clarification when language confidence is low
    language_clarification = (
        conversation_manager.check_clarification_needed(
            sentiment.get("language_confidence", 0.0)
        )
    )

    if language_clarification["clarification_needed"]:
        st.warning(
            "I’m not confident I understood your message. "
            "Could you please rephrase or provide more details?"
        )


    # Task 6: Detect ambiguous follow-up questions
    ambiguous_follow_up = detect_ambiguous_follow_up(question)

    if ambiguous_follow_up["ambiguous_follow_up"]:
        st.warning(
            "I’m not sure what you’re referring to. "
            "Could you please specify the order, product, or issue?"
        )


    # Task 6: Detect multiple requests
    multiple_requests = conversation_manager.detect_multiple_requests(
        question
    )

    if multiple_requests["multiple_requests"]:
        st.warning(
            f"I detected {multiple_requests['request_count']} separate requests. "
            "I’ll handle them separately."
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


       # 3. Add current message to conversation history
    conversation_manager.add_message(
        question,
        sentiment
    )

    # 4. Evaluate escalation using updated conversation history
    escalation = evaluate_escalation(
        question,
        sentiment,
        conversation_manager.get_history(),
        current_hour=current_hour
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

    ticket = extract_ticket_information(
       masked_ticket_question
    )

# Task 6: Apply corrected order ID
    correction = conversation_manager.detect_correction(question)

    if correction["correction_detected"]:
       corrected_order_id = conversation_manager.extract_order_id(question)

       if corrected_order_id:
          ticket["order_id"] = corrected_order_id

    missing_information = find_missing_information(
    ticket
    )


    # Task 6: Calculate intent confidence
    intent_confidence = (
        1.0 if ticket.get("issue") else 0.0
    )


    # Task 6: Request clarification when intent confidence is low
    intent_clarification = (
        conversation_manager.check_clarification_needed(
            1.0,
            intent_confidence
        )
    )

    if intent_clarification["clarification_needed"]:
        st.warning(
            "I’m not confident I understood your request. "
            "Could you please provide more details?"
        )


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
        st.success(
            "All mandatory ticket information is available."
        )


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
    sla_escalation = handle_sla_escalation(
        ticket_sla
    )

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

        response =  answer_question(
            masked_question,
            customer_access_level=customer_access_level,
            target_date=historical_date
        )


        response_latency_ms = round(
            (time.time() - response_start_time) * 1000,
            2
        )


        monitoring_metrics = record_monitoring_metrics(
            latency_ms=response_latency_ms,
            failure_count=response_failure_count,
            confidence_score=sentiment["confidence"],
            escalation_count=(
                1 if escalation["escalation_required"]
                else 0
            )
        )


        st.subheader("Task 3 Monitoring")

        st.write(
            f"Response Latency: "
            f"{monitoring_metrics['latency_ms']} ms"
        )

        st.write(
            f"Failures: "
            f"{monitoring_metrics['failure_count']}"
        )

        st.write(
            f"Confidence: "
            f"{monitoring_metrics['confidence_score']}"
        )

        st.write(
            f"Escalations: "
            f"{monitoring_metrics['escalation_count']}"
        )


        if response["grounded"]:

            st.write(
                response["answer"]
            )

            st.subheader("Sources")

            for citation in response["citations"]:
                st.write(citation)

        else:

            st.warning(
                "⚠️ I don't have enough reliable evidence "
                "to answer this question. "
                "Please clarify your question or provide "
                "additional information."
            )


    except Exception as e:

        response_failure_count = 1

        error_message = str(e)

        if (
            "429" in error_message
            or "RESOURCE_EXHAUSTED" in error_message
        ):

            st.warning(
                "The chatbot's AI response service is "
                "temporarily unavailable because the API "
                "request quota has been reached. "
                "The sentiment and escalation analysis "
                "is still available."
            )

        else:

            st.exception(e)


    # 9. Conversation summary
    st.subheader("Conversation Summary")

    st.write(
        escalation["conversation_summary"]
    )