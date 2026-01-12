# 🤖 AI-Powered Knowledge Engine for Smart Support and Ticket Resolution

A complete **ticket resolution system** powered by a **Retrieval-Augmented Generation (RAG)** model.  
It leverages **Streamlit** for the interface, **FAISS** for vector search, **Sentence Transformers** for embeddings, and the **Groq API** for ultra-fast LLM inference.

---

## ✨ Features

- 💬 **Chatbot Interface** — Conversational AI that answers queries from your knowledge base.  
- 📊 **Feedback Logging** — Records user feedback to **Google Sheets** to track performance and identify gaps.  
- 📈 **Analytics Dashboard** — Displays query statistics, resolution rates, and model performance metrics.  
- 📧 **Email Alerts** — Automatically sends **PDF reports** of unresolved queries to configured emails.  

---

## ⚙️ Setup Instructions

```bash
https://github.com/Nidhi-o/AI-Powered-Knowledge-Engine-for-Smart-Support-and-Ticket-Resolution.git
cd AI-Powered-Knowledge-Engine-for-Smart-Support-and-Ticket-Resolution
```
### Create a Virtual Environment

It’s recommended to isolate dependencies using a virtual environment.

```bash
# Create the environment (Python 3.10+ is recommended)
conda create --name ticket_res_env python=3.10 -y

# Activate the environment
conda activate ticket_res_env
```

---

### Create the Vector Index

Before running the main app, process the corpus and build the FAISS vector index:

```bash
python create_index.py
```

This will generate:

```
faiss_index.bin
corpus_data.pkl
```

---

### Run the Streamlit Application

Finally, launch the app:

```bash
streamlit run app.py
```

Then open your browser and visit the local Streamlit URL (usually `http://localhost:8501`).

---

## 🧠 Tech Stack

| Component | Technology |
|------------|-------------|
| Frontend | Streamlit |
| Embeddings | Sentence Transformers |
| Vector Search | FAISS |
| LLM Inference | Groq API |
| Data Storage | Google Sheets |
| Reports | FPDF / smtplib |

---

## 🔮 Future Enhancements

- 🧩 Multi-user authentication  
- 📂 Notion / Airtable integration for ticket tracking  
- 🔊 Voice-based ticket submission  
- 🕒 Chat memory persistence across sessions  

---

## 🪪 License

This project is licensed under the **MIT License**.  
© 2025 [Nidhi Dhankarghare](https://github.com/Nidhi-o)

---
