import streamlit as st
from datetime import datetime

from langchain_helper import get_qa_chain, create_vector_db
from sentiment_engine import analyze_sentiment
from conversation_manager import ConversationManager
from escalation_engine import evaluate_escalation


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
question = st.text_input("Question: ")


if question and question != st.session_state.get("last_question"):
    st.session_state["last_question"] = question

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

    # 8. Generate chatbot response
    # 8. Generate chatbot response
st.header("Answer")

try:
    chain = get_qa_chain()
    response = chain(question)
    st.write(response["result"])

except Exception as e:
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