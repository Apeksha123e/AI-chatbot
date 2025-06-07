import streamlit as st
import google.generativeai as genai

genai.configure(api_key="AIzaSyDLTusDd6HEbWnbZlWUS8a-4fUA2NI4jI4")

model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

st.set_page_config(page_title="AI Chatbot 💬", layout="centered")
st.title("🤖 AI Chatbot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


user_input = st.text_input("You:", key="user_input")

if st.button("Send") and user_input:
    
    st.session_state.chat_history = []

    st.session_state.chat_history.append(("You", user_input))

    try:
        response = model.generate_content(user_input)
        reply = response.text.strip()
    except Exception as e:
        reply = f"❌ Error: {e}"

   
    st.session_state.chat_history.append(("AI", reply))
    st.rerun()

if st.session_state.chat_history:
    for speaker, message in st.session_state.chat_history:
        if speaker == "You":
            st.markdown(f"**🧑‍💻 {speaker}:** {message}")
        else:
            st.markdown(f"**🤖 {speaker}:** {message}")
