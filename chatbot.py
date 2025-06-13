import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
from langdetect import detect
from io import BytesIO
from fpdf import FPDF
import pyttsx3
import json
from datetime import datetime

# --- Gemini API Configuration ---
genai.configure(api_key="AIzaSyDLTusDd6HEbWnbZlWUS8a-4fUA2NI4jI4")
model = genai.GenerativeModel("models/gemini-1.5-flash")

# --- Page Config ---
st.set_page_config(page_title="AI Chatbot + PDF Assistant", layout="wide")

# --- Title ---
st.markdown("""
# 🤖 AI Chatbot + 📄 PDF Assistant
### Powered by Gemini API
---
""")

# --- Session States ---
for key in ["pdf_text", "summary", "topics", "flashcards", "answer", "last_q", "last_a", "view"]:
    if key not in st.session_state:
        st.session_state[key] = ""
if "input_counter" not in st.session_state:
    st.session_state.input_counter = 0
if "history" not in st.session_state:
    st.session_state.history = []

# --- Sidebar ---
st.sidebar.header("📋 Navigation")
selected_tab = st.sidebar.radio("Choose a Tool", ["💬 Chatbot", "📄 Summarize PDF", "📚 Topics", "🧠 Flashcards", "❓ Ask PDF"])

pdf_file = st.sidebar.file_uploader("📄 Upload a PDF", type=["pdf"])
if pdf_file:
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = "".join(page.get_text() for page in doc)
    st.session_state.pdf_text = text
    try:
        lang = detect(text)
        st.sidebar.success(f"Language Detected: {lang.upper()}")
    except:
        st.sidebar.warning("Language detection failed.")

    # Save PDF upload event
    st.session_state.history.append({
        "type": "pdf_upload",
        "filename": pdf_file.name,
        "timestamp": str(datetime.now())
    })

# --- Chatbot ---
if selected_tab == "💬 Chatbot":
    st.subheader("💬 Chat with AI")

    input_key = f"chat_input_{st.session_state.input_counter}"
    user_input = st.text_input("You:", key=input_key, placeholder="Ask anything...")

    if st.button("Send"):
        if user_input.strip() != "":
            try:
                response = model.generate_content(user_input)
                reply = response.text.strip()

                st.session_state.last_q = user_input
                st.session_state.last_a = reply

                st.session_state.history.append({
                    "type": "chat",
                    "user": user_input,
                    "bot": reply,
                    "timestamp": str(datetime.now())
                })

                st.session_state.input_counter += 1
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {e}")
        else:
            st.warning("Please enter a message.")

    if st.session_state.last_q:
        st.markdown(f"**🧑‍💻 You:** {st.session_state.last_q}")
        st.markdown(f"**🤖 AI:** {st.session_state.last_a}")

# --- PDF Summary ---
elif selected_tab == "📄 Summarize PDF":
    st.subheader("📄 PDF Summary")
    if st.session_state.pdf_text:
        if st.button("🔍 Summarize PDF"):
            try:
                response = model.generate_content(f"Summarize this:\n{st.session_state.pdf_text}")
                summary = response.text.strip()
                st.session_state.summary = summary

                st.session_state.history.append({
                    "type": "pdf_summary",
                    "summary": summary,
                    "timestamp": str(datetime.now())
                })

            except Exception as e:
                st.session_state.summary = f"❌ Error: {e}"

        if st.session_state.summary:
            st.markdown("### 📝 Summary")
            st.code(st.session_state.summary, language="text")

            if st.button("📤 Export Summary as PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for line in st.session_state.summary.split('\n'):
                    pdf.multi_cell(0, 10, line)
                output = BytesIO()
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                output.write(pdf_bytes)
                output.seek(0)
                st.download_button("Download Summary PDF", data=output, file_name="summary.pdf", mime="application/pdf")

            if st.button("📤 Export as TXT"):
                txt_output = BytesIO(st.session_state.summary.encode())
                st.download_button("Download TXT", data=txt_output, file_name="summary.txt", mime="text/plain")

            if st.button("🔊 Read Aloud"):
                engine = pyttsx3.init()
                engine.say(st.session_state.summary)
                engine.runAndWait()
    else:
        st.info("📄 Please upload a PDF in the sidebar.")

# --- Topic Detection ---
elif selected_tab == "📚 Topics":
    st.subheader("📚 Detect Topics from PDF")
    if st.session_state.pdf_text:
        if st.button("📚 Detect Topics"):
            try:
                response = model.generate_content(f"List key topics from this:\n{st.session_state.pdf_text}")
                topics = response.text.strip()
                st.session_state.topics = topics

                st.session_state.history.append({
                    "type": "pdf_topics",
                    "topics": topics,
                    "timestamp": str(datetime.now())
                })

            except Exception as e:
                st.session_state.topics = f"❌ Error: {e}"
        if st.session_state.topics:
            st.markdown("### 🧩 Topics")
            st.code(st.session_state.topics)
    else:
        st.info("📄 Please upload a PDF in the sidebar.")

# --- Flashcards ---
elif selected_tab == "🧠 Flashcards":
    st.subheader("🧠 Generate Flashcards")
    if st.session_state.pdf_text:
        if st.button("🧠 Generate Flashcards"):
            try:
                response = model.generate_content(f"Create flashcards from this:\n{st.session_state.pdf_text}")
                flashcards = response.text.strip()
                st.session_state.flashcards = flashcards

                st.session_state.history.append({
                    "type": "pdf_flashcards",
                    "flashcards": flashcards,
                    "timestamp": str(datetime.now())
                })

            except Exception as e:
                st.session_state.flashcards = f"❌ Error: {e}"
        if st.session_state.flashcards:
            st.markdown("### 🧠 Flashcards")
            st.code(st.session_state.flashcards)
    else:
        st.info("📄 Please upload a PDF in the sidebar.")

# --- Question Answering ---
elif selected_tab == "❓ Ask PDF":
    st.subheader("❓ Ask Questions from PDF")
    if st.session_state.pdf_text:
        question = st.text_input("Your question about the PDF")
        if st.button("Ask"):
            try:
                response = model.generate_content(f"Text:\n{st.session_state.pdf_text}\n\nQuestion: {question}")
                answer = response.text.strip()
                st.session_state.answer = answer

                st.session_state.history.append({
                    "type": "pdf_qa",
                    "question": question,
                    "answer": answer,
                    "timestamp": str(datetime.now())
                })

            except Exception as e:
                st.session_state.answer = f"❌ Error: {e}"
        if st.session_state.answer:
            st.markdown("### 🤖 Answer")
            st.code(st.session_state.answer)
    else:
        st.info("📄 Please upload a PDF in the sidebar.")

# --- Export All History ---
st.sidebar.markdown("---")
if st.sidebar.button("💾 Export All History as JSON"):
    history_json = json.dumps(st.session_state.history, indent=2)
    history_bytes = BytesIO(history_json.encode("utf-8"))
    st.sidebar.download_button("📥 Download History JSON", data=history_bytes, file_name="chat_pdf_history.json", mime="application/json")

# --- Footer ---
st.markdown("---")

