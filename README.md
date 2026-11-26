# Real-Time Gen AI Customer Service Chatbot

## Project Overview

This project is a Real-Time Generative AI Customer Service Chatbot designed to assist customers with common service-related queries while providing grounded, secure, and context-aware responses.

The system combines Retrieval-Augmented Generation (RAG), sentiment analysis, escalation handling, multimodal evidence processing, and support ticket generation.

## Key Features

- 🤖 Generative AI customer service chatbot
- 📚 RAG-based knowledge retrieval
- 🔐 Grounded responses using verified information
- 😊 Customer sentiment analysis
- 🚨 Automatic escalation and priority detection
- 📎 Evidence upload and processing
- 🎫 Support ticket generation
- 🧾 Evidence integration into customer tickets
- 🛡️ Protection against prompt injection and unsupported claims
- 📊 Response grounding and source citations
- 🌐 Streamlit-based user interface

## Technologies Used

- Python
- Streamlit
- LangChain
- Google Gemini
- FAISS
- NLP
- NLTK
- TextBlob
- OCR / Tesseract
- Python-dotenv

## Project Structure

```text
CUSTOMER_SERVICE_CHATBOT_LLM/
│
├── src/
│   ├── main.py
│   ├── langchain_helper.py
│   ├── rag_knowledge_engine.py
│   ├── sentiment_engine.py
│   ├── escalation_engine.py
│   ├── multimodal_evidence_engine.py
│   ├── support_ticket_engine.py
│   └── conversation_manager.py
│
├── faiss_index/
├── requirements.txt
└── README.md
