#**RAG-based Ticket Resolution System**

This project is a complete ticket resolution system powered by a Retrieval-Augmented Generation (RAG) model. It uses Streamlit for the user interface, FAISS for vector search, Sentence Transformers for embeddings, and the Groq API for fast language model inference.

Features

Chatbot Interface: A conversational AI to answer user queries based on a provided knowledge base.

Feedback Mechanism: Logs user feedback to Google Sheets to track model performance and identify knowledge gaps.

Analytics Dashboard: Visualizes query statistics, resolution rates, and model activity.

Email Alerts: Automatically generates and sends PDF reports on unresolved queries to designated emails.

Setup Instructions

1. Create a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

# Create the virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate


2. Install Dependencies

Install all the required Python packages from the requirements.txt file.

pip install -r requirements.txt


3. Configure Environment Variables

This project requires several API keys and configuration details.

Create a file named .env in the root directory of the project.

Copy the contents of .env.example into your new .env file.

Fill in the values for each variable.

Variable Details:

GROQ_API_KEY: Your API key from the Groq console.

GOOGLE_SHEETS_CREDENTIALS: The entire content of your Google Cloud service account JSON file. This is a multi-line variable.

RESOLVED_SHEET_URL: The URL of the Google Sheet for logging resolved queries.

KNOWLEDGE_GAP_SHEET_URL: The URL of the Google Sheet for logging unresolved queries.

EMAIL_HOST: Your email provider's SMTP server (e.g., smtp.gmail.com).

EMAIL_PORT: The SMTP port (e.g., 587 for TLS).

EMAIL_USER: The email address from which alerts will be sent.

EMAIL_PASSWORD: Your email password or an "App Password" if you have 2-Factor Authentication enabled.

4. Set Up Google Sheets

Enable the Google Sheets API in your Google Cloud project.

Create a service account and download the JSON credentials file.

Create two Google Sheets: one for resolved queries and one for knowledge gaps.

Share both sheets with the client_email found in your service account JSON file, giving it "Editor" permissions.

Add the following headers to the first row of each sheet:

Resolved Sheet: ID, Query, Solution, Generated Answer, Status, Timestamp

Knowledge Gap Sheet: ID, Query, Model Answer, Status, Timestamp

5. Prepare Your Corpus

Place your knowledge base file in the root directory and name it corpus.xlsx.

Ensure it has two columns: Query and Solution.

6. Create the Vector Index

Before running the main app, you need to process your corpus and create the FAISS vector index. This is a one-time step (unless you update your corpus).

python create_index.py


This will create two files: faiss_index.bin and corpus_data.pkl.

7. Run the Streamlit Application

You are now ready to launch the application.

streamlit run app.py


Open your web browser and navigate to the local URL provided by Streamlit.
