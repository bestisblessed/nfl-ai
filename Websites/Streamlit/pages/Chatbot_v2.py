import streamlit as st
from openai import OpenAI
import time
from dotenv import load_dotenv
from IPython.display import Image

st.title('NFL AI Chatbot')

# client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Sidebar input for OpenAI API key
OPENAI_API_KEY = st.sidebar.text_input("Enter your OpenAI API key:", type='password')
if OPENAI_API_KEY:
    # run_nfl_chatbot(OPENAI_API_KEY)
    client = OpenAI(api_key=OPENAI_API_KEY)
    file1 = client.files.create(
        file=open("Streamlit/data/Teams.csv", "rb"),
        purpose='assistants'
    )
    file2 = client.files.create(
        file=open("Streamlit/data/Games.csv", "rb"),
        purpose='assistants'
    )
    file3 = client.files.create(
        file=open("Streamlit/data/PlayerStats.csv", "rb"),
        purpose='assistants'
    )
    assistant = client.beta.assistants.create(
        name="Football Buddy Streamlit gpt4o",
        instructions="""You are a data analyst and machine learning expert. Help the user analyze, visualize and explore trends using all ofthe NFL data in your knowledge base files. You are to use this knowledge base to answer all the users questions and for your data analysis and answers. First, always begin new threads by loading all the files in your knowledge base into dataframes and examining them to learn the structure and  every single column name and data/variable you have available. Take a look at the first and last few rows of each dataset to better learn the structure of each variable. Then proceed with answering the users questions.""",
        tools=[{"type": "code_interpreter"}],
        model="gpt-4o",
        tool_resources={
            "code_interpreter": {
                "file_ids": [file1.id, file2.id, file3.id]
            }
        }
    )
    st.write(assistant)
else:
    st.error("Please enter your OpenAI API key in the sidebar.")

# if "openai_model" not in st.session_state:
#     st.session_state["openai_model"] = "gpt-3.5-turbo"

# Initialize the message history in session state if not already present
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages in the chat interface
for message in st.session_state.messages:
    st.chat_message(message["role"]).markdown(message["content"])

# Capture and handle user input
if user_question := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": user_question})
    st.chat_message("user").markdown(user_question)

    # Initialize or continue the thread
    if 'thread_id' not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state['thread_id'] = thread.id
        st.write('Thread Info: ', thread)
    else:
        # st.write('Continuing conversation in Thread ID: ', st.session_state['thread_id'])
        st.write('')
    
    # Send user message to the assistant
    message = client.beta.threads.messages.create(
        thread_id=st.session_state['thread_id'],
        role="user",
        content=user_question,
    )

    # Run the assistant response
    run = client.beta.threads.runs.create(
        thread_id=st.session_state['thread_id'],
        assistant_id=assistant.id,
    )
    
    with st.spinner('Processing...'):
        while run.status != "completed":
            time.sleep(10)
            run = client.beta.threads.runs.retrieve(thread_id=st.session_state['thread_id'], run_id=run.id)
        
    st.success('Done!')

    # Retrieve messages from the thread
    messages = client.beta.threads.messages.list(
        thread_id=st.session_state['thread_id']
    )

    # Process and display each message
    for message in reversed(messages.data):
        if hasattr(message.content[0], 'text'):
            content = message.content[0].text.value
            role = message.role
            st.session_state.messages.append({"role": role, "content": content})
            st.chat_message(role).markdown(content)
        elif hasattr(message.content[0], 'image_file'):
            st.write(message.role + ": [image file received]")
            new_file = message.content[0].image_file.file_id
            image_data = client.files.content(new_file)
            image_data_bytes = image_data.read()
            st.image(image_data_bytes)
        else:
            st.write(message.role + ": [Unsupported content type]")