import streamlit as st
from openai import OpenAI
import time
from dotenv import load_dotenv
from IPython.display import Image

st.title('NFL AI Chatbot')

def run_nfl_chatbot(OPENAI_API_KEY):
    # Initialize OpenAI client with just the API key
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url="https://api.openai.com/v1"  # Optional but explicit
    )

    # file1 = client.files.create(
    #     file=open("Streamlit/data/Teams.csv", "rb"),
    #     purpose='assistants'
    # )
    # file2 = client.files.create(
    #     file=open("Streamlit/data/Games.csv", "rb"),
    #     purpose='assistants'
    # )
    # file3 = client.files.create(
    #     file=open("Streamlit/data/PlayerStats.csv", "rb"),
    #     purpose='assistants'
    # )
    # assistant = client.beta.assistants.create(
    #     name="Football Buddy Streamlit gpt4o",
    #     instructions="""You are a data analyst and machine learning expert. Help the user analyze, visualize and explore trends using all ofthe NFL data in your knowledge base files. You are to use this knowledge base to answer all the users questions and for your data analysis and answers. First, always begin new threads by loading all the files in your knowledge base into dataframes and examining them to learn the structure and  every single column name and data/variable you have available. Take a look at the first and last few rows of each dataset to better learn the structure of each variable. Then proceed with answering the users questions.""",
    #     tools=[{"type": "code_interpreter"}],
    #     model="gpt-4o",
    #     tool_resources={
    #         "code_interpreter": {
    #             "file_ids": [file1.id, file2.id, file3.id]
    #         }
    #     }
    # )
    # st.write(assistant)
    
    assistant_nfl = 'asst_o94cCYcWOKHRDkuGJiEyvzhM'
    # assistant_nfl_gpt4omini = 'asst_W7LKh5Vp6eRu6e2EZlaDt2Sn'
    assistant = client.beta.assistants.retrieve(assistant_nfl)
    
    if 'thread_id' not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state['thread_id'] = thread.id
        st.write('Thread Info: ', thread)
    else:
        st.write('Continuing conversation in Thread ID: ', st.session_state['thread_id'])

    # user_question = st.text_input("Enter your question:", "")
    user_question = st.chat_input("Say something")
    
    if user_question:
        st.write(f"User 🙋‍♂️: {user_question}")
        # with st.chat_message("user"):
        #     st.write(f"User has sent the following prompt: {user_question}")
        message = client.beta.threads.messages.create(
            thread_id=st.session_state['thread_id'],
            role="user",
            content=user_question,
        )
        run = client.beta.threads.runs.create(
            thread_id=st.session_state['thread_id'],
            assistant_id=assistant.id,
        )
        with st.spinner('Processing...'):
            while run.status != "completed":
                time.sleep(10)
                run = client.beta.threads.runs.retrieve(thread_id=st.session_state['thread_id'], run_id=run.id)
        
        st.success('Done!')
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state['thread_id']
        )
        
        for message in reversed(messages.data):
            if hasattr(message.content[0], 'text'):
                st.write(message.role + ": " + message.content[0].text.value)
            elif hasattr(message.content[0], 'image_file'):
                st.write(message.role + ": [image file received]")
            else:
                st.write(message.role + ": [Unsupported content type]")
        
        if hasattr(message.content[0], 'image_file'):
            new_file = messages.data[0].content[0].image_file.file_id
            st.write("file id: ", new_file)
            image_data = client.files.content(new_file)
            image_data_bytes = image_data.read()
            st.image(image_data_bytes)
        else:
            st.markdown('<p style="font-size:12px; font-style:italic;">No image</p>', unsafe_allow_html=True)


# Sidebar input for OpenAI API key
OPENAI_API_KEY = st.sidebar.text_input("Enter your OpenAI API key:", type='password')

if OPENAI_API_KEY:
    run_nfl_chatbot(OPENAI_API_KEY)
else:
    st.error("Please enter your OpenAI API key in the sidebar.")








# ### WORKING GPT3 v1 API
# # if api_key_input:
# #     openai.api_key = api_key_input
# #     client = openai.OpenAI(api_key=api_key_input)

# #     # You can now safely proceed with the rest of your app

# #     # assistant_football_buddy = 'asst_5fmtrcAh2FMGhFjUaWYHOqow'
# #     assistant_football_buddy_GPT_3_Turbo = 'asst_dF6eUKIKhbtmSVUcKAXy6y8v'
# #     assistant = client.beta.assistants.retrieve(assistant_football_buddy_GPT_3_Turbo)

# #     st.title('NFL Chatbot')

# #     ### --- CHAT ---- ###
# #     user_question = st.text_input("Enter your question:", "")

# #     if user_question:
# #         # Create thread
# #         thread = client.beta.threads.create()
# #         st.write('Thread Info: ', thread)

# #         # Add message to thread
# #         message = client.beta.threads.messages.create(
# #             thread_id=thread.id,
# #             role="user",
# #             content=user_question,
# #         )

# #         # Run it 
# #         run = client.beta.threads.runs.create(
# #             thread_id=thread.id,
# #             assistant_id=assistant.id,
# #         )

# #         with st.spinner('Processing...'):
# #             # Wait for completion 
# #             while run.status != "completed":
# #                 time.sleep(2)
# #                 run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

# #         st.success('Done!')

# #         # Display assistant response
# #         messages = client.beta.threads.messages.list(thread_id=thread.id)

# #         st.write('All Messages: ')
# #         for message in reversed(messages.data):
# #             if hasattr(message.content[0], 'text'):
# #                 st.write(message.role + ": " + message.content[0].text.value)
# #             elif hasattr(message.content[0], 'image_file'):
# #                 st.write(message.role + ": [Image file received]")
# #             else:
# #                 st.write(message.role + ": [Unsupported content type]")

# #         # Check if an image file is available
# #         if hasattr(message.content[0], 'image_file'):
# #             new_file = messages.data[0].content[0].image_file.file_id

# #             # Download files created by assistant
# #             image_data = client.files.content(new_file)
# #             image_data_bytes = image_data.read()

# #             # Display images and files downloaded
# #             st.image(image_data_bytes)
# #         else:
# #             st.write('No image :(')
# # else:
# #     st.error("Please enter your OpenAI API Key in the sidebar.")

