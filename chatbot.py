import streamlit as st
import json
import bcrypt
import os
from datetime import datetime
import google.generativeai as genai
import fitz  # PyMuPDF
from langdetect import detect
from io import BytesIO
from fpdf import FPDF
# import pyttsx3


st.set_page_config(page_title="AI Chatbot + PDF Assistant", layout="wide")


def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)["users"]
    return []

def save_user(name, username, password):
    users = load_users()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users.append({"name": name, "username": username, "password": hashed})
    with open("users.json", "w") as f:
        json.dump({"users": users}, f)

def authenticate_user(username, password):
    users = load_users()
    for user in users:
        if user["username"] == username and bcrypt.checkpw(password.encode(), user["password"].encode()):
            return user["name"]
    return None


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "name" not in st.session_state:
    st.session_state.name = ""

if not st.session_state.logged_in:
    st.title("🤖 AI Chatbot + 📄 PDF Assistant")
    st.subheader("“Your intelligent assistant for documents and discussions.”")
    st.markdown("---")

    action = st.radio("Choose an option", ["Login", "Sign Up"], horizontal=True)

    if action == "Login":
        login_user = st.text_input("Username")
        login_pass = st.text_input("Password", type="password")
        if st.button("🔐 Login"):
            name = authenticate_user(login_user, login_pass)
            if name:
                st.session_state.logged_in = True
                st.session_state.name = name
                st.rerun()
            else:
                st.error("Invalid username or password.")

    elif action == "Sign Up":
        new_name = st.text_input("Name")
        new_user = st.text_input("Choose a username")
        new_pass = st.text_input("Choose a password", type="password")
        if st.button("📝 Register"):
            if new_name and new_user and new_pass:
                existing = [u["username"] for u in load_users()]
                if new_user in existing:
                    st.warning("Username already exists. Try logging in.")
                else:
                    save_user(new_name, new_user, new_pass)
                    st.success("Account created! Please login.")
            else:
                st.warning("Please fill all fields.")

    st.stop()


st.sidebar.write(f"👋 Welcome, {st.session_state.name}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.name = ""
    st.rerun()


genai.configure(api_key="AIzaSyDLTusDd6HEbWnbZlWUS8a-4fUA2NI4jI4")
model = genai.GenerativeModel("models/gemini-1.5-flash")


st.title("🤖 AI Chatbot + 📄 PDF Assistant")
st.markdown("---")


for key in ["pdf_text", "summary", "topics", "flashcards", "answer", "last_q", "last_a"]:
    st.session_state.setdefault(key, "")
st.session_state.setdefault("input_counter", 0)
st.session_state.setdefault("history", [])

st.sidebar.header("📋 Navigation")
tab = st.sidebar.radio("Choose a Tool", ["💬 Chatbot", "📄 Summarize PDF", "📚 Topics", "🧠 Flashcards", "❓ Ask PDF"])

pdf_file = st.sidebar.file_uploader("📄 Upload PDF", type="pdf")
if pdf_file:
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = "".join(page.get_text() for page in doc)
    st.session_state.pdf_text = text
    try:
        lang = detect(text)
        st.sidebar.success(f"Detected Language: {lang.upper()}")
    except:
        st.sidebar.warning("Language detection failed.")
    st.session_state.history.append({
        "type": "pdf_upload",
        "filename": pdf_file.name,
        "timestamp": str(datetime.now())
    })


if tab == "💬 Chatbot":
    st.subheader("💬 Chat with AI")
    input_key = f"chat_input_{st.session_state.input_counter}"
    user_input = st.text_input("You:", key=input_key, placeholder="Ask anything...")
    if st.button("Send"):
        if user_input.strip():
            try:
                response = model.generate_content(user_input)
                reply = response.text.strip()
                st.session_state.last_q = user_input
                st.session_state.last_a = reply
                st.session_state.input_counter += 1
                st.session_state.history.append({
                    "type": "chat", "user": user_input, "bot": reply,
                    "timestamp": str(datetime.now())
                })
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
    if st.session_state.last_q:
        st.markdown(f"**🧑‍💻 You:** {st.session_state.last_q}")
        st.markdown(f"**🤖 AI:** {st.session_state.last_a}")


elif tab == "📄 Summarize PDF":
    st.subheader("📄 PDF Summary")
    if st.session_state.pdf_text:
        if st.button("🔍 Summarize PDF"):
            try:
                response = model.generate_content(f"Summarize this:\n{st.session_state.pdf_text}")
                summary = response.text.strip()
                st.session_state.summary = summary
                st.session_state.history.append({
                    "type": "pdf_summary", "summary": summary,
                    "timestamp": str(datetime.now())
                })
            except Exception as e:
                st.session_state.summary = f"❌ Error: {e}"
        if st.session_state.summary:
            st.markdown("### 📝 Summary")
            st.code(st.session_state.summary)
            # if st.button("🔊 Read Aloud"):
            #     engine = pyttsx3.init()
            #     engine.say(st.session_state.summary)
            #     engine.runAndWait()
            if st.button("📤 Export Summary PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for line in st.session_state.summary.split('\n'):
                    pdf.multi_cell(0, 10, line)
                output = BytesIO()
                output.write(pdf.output(dest="S").encode("latin-1"))
                output.seek(0)
                st.download_button("Download PDF", data=output, file_name="summary.pdf", mime="application/pdf")


elif tab == "📚 Topics":
    st.subheader("📚 Detect Topics")
    if st.session_state.pdf_text:
        if st.button("📚 Detect Topics"):
            try:
                response = model.generate_content(f"List key topics:\n{st.session_state.pdf_text}")
                st.session_state.topics = response.text.strip()
                st.session_state.history.append({
                    "type": "pdf_topics", "topics": st.session_state.topics,
                    "timestamp": str(datetime.now())
                })
            except Exception as e:
                st.session_state.topics = f"❌ Error: {e}"
        if st.session_state.topics:
            st.markdown("### 🧩 Topics")
            st.code(st.session_state.topics)


elif tab == "🧠 Flashcards":
    st.subheader("🧠 Generate Flashcards")
    if st.session_state.pdf_text:
        if st.button("🧠 Generate"):
            try:
                response = model.generate_content(f"Create flashcards:\n{st.session_state.pdf_text}")
                st.session_state.flashcards = response.text.strip()
                st.session_state.history.append({
                    "type": "pdf_flashcards", "flashcards": st.session_state.flashcards,
                    "timestamp": str(datetime.now())
                })
            except Exception as e:
                st.session_state.flashcards = f"❌ Error: {e}"
        if st.session_state.flashcards:
            st.markdown("### Flashcards")
            st.code(st.session_state.flashcards)


elif tab == "❓ Ask PDF":
    st.subheader("❓ Ask Questions")
    if st.session_state.pdf_text:
        question = st.text_input("Your question:")
        if st.button("Ask"):
            try:
                response = model.generate_content(f"Text:\n{st.session_state.pdf_text}\n\nQuestion: {question}")
                st.session_state.answer = response.text.strip()
                st.session_state.history.append({
                    "type": "pdf_qa", "question": question, "answer": st.session_state.answer,
                    "timestamp": str(datetime.now())
                })
            except Exception as e:
                st.session_state.answer = f"❌ Error: {e}"
        if st.session_state.answer:
            st.markdown("### 🤖 Answer")
            st.code(st.session_state.answer)


st.sidebar.markdown("---")
if st.sidebar.button("💾 Export History"):
    history_json = json.dumps(st.session_state.history, indent=2)
    st.sidebar.download_button("📥 Download JSON", data=BytesIO(history_json.encode()), file_name="chat_pdf_history.json", mime="application/json")
