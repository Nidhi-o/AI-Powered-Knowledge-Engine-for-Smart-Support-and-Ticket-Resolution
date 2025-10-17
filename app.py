import streamlit as st
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from groq import Groq
import os
import re
import pickle
import plotly.express as px
from google_sheets_handler import GoogleSheetsHandler
from email_alert_handler import EmailAlertHandler

# --- Page Configuration ---
st.set_page_config(
    page_title="Customer Support RAG Bot",
    page_icon="🤖",
    layout="wide"
)

# --- Robust Environment Variable Loader ---
def manual_load_dotenv(dotenv_path=".env"):
    """
    Manually parses a .env file and sets environment variables.
    This version is more forgiving of formatting errors, ignoring comments,
    blank lines, and extra spaces.
    """
    if not os.path.exists(dotenv_path):
        print(f"Warning: .env file not found at {dotenv_path}. Relying on system environment variables.")
        return

    with open(dotenv_path) as f:
        for line in f:
            line = line.strip()
            # Ignore comments and blank lines
            if not line or line.startswith('#'):
                continue
            
            # Use regex to find the first '=' and split, handling potential spaces
            match = re.match(r'^\s*([\w.-]+)\s*=\s*(.*?)?\s*$', line)
            if match:
                key, value = match.groups()
                # Remove surrounding quotes from the value if they exist
                if value and ((value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'"))):
                    value = value[1:-1]
                os.environ.setdefault(key, value)

# --- Environment Setup ---
os.environ["TOKENIZERS_PARALLELISM"] = "false"
manual_load_dotenv() # Use our new robust loader instead of load_dotenv()

# --- Core RAG Functions ---
def search_faiss_index(query, index, model, corpus_data, k=3):
    """Searches the FAISS index for the most similar queries."""
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding.astype('float32'), k)
    results = []
    for i in range(len(indices[0])):
        idx = indices[0][i]
        original_query = corpus_data['queries'][idx]
        solution = corpus_data['solutions'][idx]
        results.append({"query": original_query, "solution": solution})
    return results

def generate_groq_response(user_query, search_results):
    """Generates a response using Groq based on the user query and retrieved context."""
    context = "\n\n".join([f"Query: {res['query']}\nSolution: {res['solution']}" for res in search_results])
    system_prompt = (
        "You are an expert customer support agent. Your goal is to provide a clear, concise, and friendly answer "
        "to the user's query based *only* on the provided context from the knowledge base. "
        "Do not invent new information. If the context does not contain the answer, "
        "state that you couldn't find the information and suggest they rephrase the question."
        "Format your answer for readability."
    )
    human_prompt = f"User Query: \"{user_query}\"\n\nContext from knowledge base:\n{context}"
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_prompt}
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"Error communicating with Groq API: {e}")
        return "Sorry, I encountered an error while generating a response."

# --- Caching and Initialization ---
@st.cache_resource
def load_faiss_index():
    """Loads the FAISS index from disk."""
    try:
        return faiss.read_index("faiss_index.bin")
    except Exception as e:
        st.error(f"**Error:** Failed to load FAISS index from `faiss_index.bin`. Did you run the `create_index.py` script successfully? \n\nDetails: {e}")
        return None

@st.cache_resource
def load_corpus_data():
    """Loads the corpus data (queries and solutions) from disk."""
    try:
        with open("corpus_data.pkl", "rb") as f:
            return pickle.load(f)
    except Exception as e:
        st.error(f"**Error:** Failed to load corpus data from `corpus_data.pkl`. Did you run the `create_index.py` script successfully? \n\nDetails: {e}")
        return None

@st.cache_resource
def initialize_embedding_model():
    """Initializes and returns the sentence transformer model."""
    return SentenceTransformer('all-MiniLM-L6-v2')

@st.cache_resource
def initialize_groq_client():
    """Initializes and returns the Groq client, with clear error handling."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("The `GROQ_API_KEY` is not set in your `.env` file.")
    return Groq(api_key=api_key)

@st.cache_resource
def initialize_sheets_handler():
    """Initializes and returns the Google Sheets handler, catching specific errors."""
    try:
        return GoogleSheetsHandler()
    except ValueError as e:
        st.error(
            f"**Google Sheets Connection Failed:**\n\n"
            f"`{e}`\n\n"
            "**Troubleshooting Steps:**\n"
            "1.  Ensure your `.env` file exists in the project root.\n"
            "2.  Verify the `GOOGLE_SHEETS_CREDENTIALS_BASE64` variable is correct and properly encoded.\n"
            "3.  Check the `README.md` for the correct `.env` file format."
        )
        return None

# --- Application Startup ---
try:
    # Attempt to load all critical components
    index = load_faiss_index()
    corpus_data = load_corpus_data()
    embedding_model = initialize_embedding_model()
    groq_client = initialize_groq_client()
    sheets_handler = initialize_sheets_handler()

    if not all([index, corpus_data, embedding_model, groq_client, sheets_handler]):
        st.warning("Application is not fully initialized due to the errors above. Please resolve them and refresh the page.")
        st.stop()

except ValueError as e:
    st.error(f"**Fatal Error:** {e}")
    st.stop()

st.title("AI-Powered Ticket Resolution System 🤖")

# --- UI Tabs ---
tab1, tab2, tab3 = st.tabs(["💬 Chatbot", "📊 Analytics", "📧 Email Alerts"])

# --- Chatbot Tab ---
with tab1:
    st.header("Ask a Question")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("What is your question?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base and generating answer..."):
                search_results = search_faiss_index(prompt, index, embedding_model, corpus_data)
                if not search_results:
                    response = "I couldn't find any relevant information in the knowledge base."
                else:
                    response = generate_groq_response(prompt, search_results)
                st.markdown(response)
                st.session_state.last_query = prompt
                st.session_state.last_response = response
                st.session_state.last_context = search_results[0]['solution'] if search_results else ""
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.feedback_given = False

    if "last_response" in st.session_state and not st.session_state.get("feedback_given", False):
        st.write("---")
        st.write("Was this answer helpful?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Yes, it resolved my issue", key="yes"):
                sheets_handler.log_resolved_query(
                    st.session_state.last_query, 
                    st.session_state.last_context, 
                    st.session_state.last_response
                )
                st.success("Thank you for your feedback! The query has been logged as resolved.")
                st.session_state.feedback_given = True
                st.rerun()
        with col2:
            if st.button("👎 No, this was not helpful", key="no"):
                sheets_handler.log_knowledge_gap(
                    st.session_state.last_query, 
                    st.session_state.last_response
                )
                st.error("Thank you for your feedback. This issue will be flagged for human review.")
                st.session_state.feedback_given = True
                st.rerun()

# --- Analytics Tab ---
with tab2:
    st.header("Performance Analytics")
    resolved_df = sheets_handler.get_all_data('resolved')
    gap_df = sheets_handler.get_all_data('knowledge_gap')
    if resolved_df.empty and gap_df.empty:
        st.info("No data available yet. Start using the chatbot to see analytics.")
    else:
        total_queries = len(resolved_df) + len(gap_df)
        resolved_count = len(resolved_df)
        resolution_rate = (resolved_count / total_queries * 100) if total_queries > 0 else 0
        st.subheader("Key Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Queries", f"{total_queries}")
        col2.metric("Resolved Queries", f"{resolved_count}")
        col3.metric("Resolution Rate", f"{resolution_rate:.2f}%")
        st.markdown("---")
        st.subheader("Query Resolution Status")
        if total_queries > 0:
            status_df = pd.DataFrame({'Status': ['Resolved', 'Not Resolved (Knowledge Gap)'],'Count': [len(resolved_df), len(gap_df)]})
            fig_pie = px.pie(status_df, names='Status', values='Count', title='Overall Query Status', hole=.3)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No query data for pie chart.")
        with st.expander("View Resolved Queries Log"):
            st.dataframe(resolved_df)
        with st.expander("View Knowledge Gap Log"):
            st.dataframe(gap_df)

# --- Email Alerts Tab ---
with tab3:
    # st.header("Generate & Send Knowledge Gap Report")
    # st.write("This section allows you to generate a PDF report of all unresolved queries (knowledge gaps) and email it to a designated recipient for review.")
    # recipient_email = st.text_input("Recipient's Email Address", "developer.email@example.com")
    # if st.button("Generate and Email Report"):
    #     knowledge_gap_df = sheets_handler.get_all_data('knowledge_gap')
    #     if knowledge_gap_df.empty:
    #         st.warning("No knowledge gaps to report.")
    #     else:
    #         with st.spinner("Generating PDF and sending email..."):
    #             try:
    #                 alert_handler = EmailAlertHandler()
    #                 pdf_path = alert_handler.create_knowledge_gap_pdf(knowledge_gap_df)
    #                 alert_handler.send_email_with_attachment(
    #                     recipient_email,
    #                     "Knowledge Gap Report",
    #                     "Please find the attached report detailing the knowledge gaps identified by the RAG model.",
    #                     pdf_path
    #                 )
    #                 st.success(f"Report successfully sent to {recipient_email}!")
    #             except Exception as e:
    #                 st.error(f"Failed to send email: {e}")
    
    st.header("Generate & Send Knowledge Gap Report")
    st.write(
        "This section allows you to generate a PDF report of all unresolved queries (knowledge gaps) "
        "and email it to a designated recipient for review."
    )

    recipient_email = st.text_input("Recipient's Email Address")

    if st.button("Generate and Email Report"):
        if not recipient_email:
            st.error("Please enter a valid recipient email address.")
        else:
            with st.spinner("Generating report and sending email..."):
                try:
                    # Fetch the latest data from Google Sheets
                    knowledge_gap_df = sheets_handler.get_all_data('knowledge_gap')

                    if knowledge_gap_df.empty:
                        st.warning("No knowledge gaps to report. The sheet is empty.")
                        # return

                    # Create the PDF report using the handler
                    email_handler=EmailAlertHandler()
                    pdf_path = email_handler.create_knowledge_gap_pdf(knowledge_gap_df)
                    
                    if pdf_path:
                        # Send the email with the generated PDF
                        email_handler.send_email_with_attachment(recipient_email, pdf_path)
                        st.success(f"Email report sent successfully to {recipient_email}!")
                    else:
                        st.error("Failed to create the PDF report.")

                except Exception as e:
                    st.error(f"Failed to send email: {e}")


