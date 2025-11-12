# streamlit_app_assistants.py
import streamlit as st
from openai import OpenAI
import time
from utils.footer import render_footer

st.title("CSV Analyst – Code Interpreter via Assistants API")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Upload your CSV files once at startup
if "file_ids" not in st.session_state:
    uploaded = []
    for filename in ["data1.csv", "data2.csv"]:
        with open(filename, "rb") as f:
            uploaded.append(client.files.create(file=f, purpose="assistants"))
    st.session_state.file_ids = [f.id for f in uploaded]

# Create (or reuse) an assistant that has the code_interpreter tool
if "assistant_id" not in st.session_state:
    assistant = client.beta.assistants.create(
        name="DataBot",
        model="gpt-4.1",
        tools=[{"type": "code_interpreter"}],
        file_ids=st.session_state.file_ids,
    )
    st.session_state.assistant_id = assistant.id

# Display chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question about your CSVs"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    # Create a new thread and run
    thread = client.beta.threads.create(messages=[{"role": "user", "content": prompt}])
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=st.session_state.assistant_id
    )

    # Retrieve and stream the run output
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    last = messages.data[0].content[0].text.value
    st.chat_message("assistant").markdown(last)

    st.session_state.messages.append({"role": "assistant", "content": last})

# Footer
render_footer()
