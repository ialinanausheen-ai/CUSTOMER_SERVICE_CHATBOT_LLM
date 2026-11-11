import os
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders.csv_loader import CSVLoader

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)

from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import RetrievalQA


# ============================================================
# 1. LOAD API KEY FROM THIS PROJECT'S SEPARATE .env FILE
# ============================================================
load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"),
    override=True
)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. Please check src/.env"
    )

# LangChain Google integration can use GOOGLE_API_KEY
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY


# ============================================================
# 2. CREATE GEMINI CHAT MODEL
# ============================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0.1,
    google_api_key=GEMINI_API_KEY,
)


# ============================================================
# 3. CREATE GEMINI EMBEDDINGS
# ============================================================

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2-preview",
    google_api_key=GEMINI_API_KEY,
)


# ============================================================
# 4. LOCATION WHERE FAISS DATABASE WILL BE SAVED
# ============================================================

vectordb_file_path = "faiss_index"


# ============================================================
# 5. CREATE VECTOR DATABASE
# ============================================================

def create_vector_db():

    # Load FAQ data from CSV file
    loader = CSVLoader(
        file_path="dataset/dataset.csv",
        source_column="prompt"
    )

    data = loader.load()

    print("Number of documents loaded:", len(data))

    # Create FAISS vector database
    vectordb = FAISS.from_documents(
        documents=data,
        embedding=embeddings
    )

    # Save vector database locally
    vectordb.save_local(vectordb_file_path)

    print("Vector database created successfully!")


# ============================================================
# 6. CREATE QUESTION-ANSWER CHAIN
# ============================================================

def get_qa_chain():

    # Load the saved FAISS database
    vectordb = FAISS.load_local(
        vectordb_file_path,
        embeddings,
        allow_dangerous_deserialization=True
    )

    # Create retriever
    retriever = vectordb.as_retriever(
        search_kwargs={"k": 3}
    )

    # Prompt for chatbot
    prompt_template = """
Given the following context and a question, generate an answer
based on this context only.

Try to provide the answer from the "response" section of the
source document without making unnecessary changes.

If the answer is not found in the context, kindly state:
"I don't know."

Do not make up an answer.

CONTEXT:
{context}

QUESTION:
{question}
"""

    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    # Create Retrieval QA chain
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={
            "prompt": PROMPT
        }
    )

    return chain


# ============================================================
# 7. TEST THE CHATBOT
# ============================================================

if __name__ == "__main__":

    create_vector_db()

    chain = get_qa_chain()

    response = chain.invoke({
        "query": "What is this course about?"
    })

    print("\nCHATBOT RESPONSE:")
    print(response["result"])