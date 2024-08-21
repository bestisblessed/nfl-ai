import streamlit as st
import openai
from openai import OpenAI
import os
import requests
import time
from dotenv import load_dotenv
from IPython.display import Image

st.title('NFL Chatbot')

# Sidebar input for API key
api_key_input = st.sidebar.text_input("Enter your OpenAI API Key:", type="password")

# Determine the correct file path prefix
if os.path.exists('data/Games.csv'):
    file_path_prefix = 'data/'
else:
    file_path_prefix = 'Streamlit/data/'

if api_key_input:
    client = OpenAI(api_key=api_key_input)

    # Store the assistant in a session state to avoid recreating it
    if 'assistant_id' not in st.session_state:
        file1 = client.files.create(
            file=open(file_path_prefix + "Games.csv", "rb"),
            purpose='assistants'
        )
        file2 = client.files.create(
            file=open(file_path_prefix + "Teams.csv", "rb"),
            purpose='assistants'
        )
        file3 = client.files.create(
            file=open(file_path_prefix + "PlayerStats.csv", "rb"),
            purpose='assistants'
        )

        assistant = client.beta.assistants.create(
            name="Football Buddy Streamlit gpt4o",
            instructions="""
                You are a data analyst and machine learning expert. You are going to help me analyze and find trends in data about NFL that I have collected that we will be later 
                using for general and deep analysis and in predictive modeling. You have a knowledge base of different NFL data from 2000-current season with game statistics and player statistics for all those games. 
                You are to use this knowledge base to answer all the users questions and for your data analysis and answers. First, always begin new conversations by loading all the files in your knowledge base into dataframes and
                examining them to learn the structure and identify every single column name and data/variable you have available. Take a look at the first and last few rows of each dataset to better learn the structure of each variable
                as well. Then do additional exploratory data analysis and descriptive statistics to help train yourself on the dataset more. When you are finished - summarize everything in 1-2 sentences for each file and list all the column names
                in each file with a short description for each column to the user. Then, tell them you are ready to help and answer questions. Use all the knowledge you have learned of the datasets to best formulate answers.""",
            tools=[{"type": "code_interpreter"}],
            model="gpt-4o",
            tool_resources={
                "code_interpreter": {
                    "file_ids": [file1.id, file2.id, file3.id]
                }
            }
        )
        st.session_state['assistant_id'] = assistant.id

    # Retrieve the assistant ID from session state
    assistant_id = st.session_state['assistant_id']

    ### --- CHAT ---- ###
    user_question = st.text_input("Enter your question:", "")

    if user_question:
        # Store thread ID in session state to maintain the same conversation
        if 'thread_id' not in st.session_state:
            thread = client.beta.threads.create()
            st.session_state['thread_id'] = thread.id

        thread_id = st.session_state['thread_id']

        # Add message to thread
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_question,
        )

        # Run it
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )

        with st.spinner('Processing...'):
            # Wait for completion 
            while run.status != "completed":
                time.sleep(2)
                run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        st.success('Done!')

        # Display assistant response
        messages = client.beta.threads.messages.list(thread_id=thread_id)

        st.write('All Messages: ')
        for message in reversed(messages.data):
            if hasattr(message.content[0], 'text'):
                st.write(message.role + ": " + message.content[0].text.value)
            elif hasattr(message.content[0], 'image_file'):
                st.write(message.role + ": [Image file received]")
            else:
                st.write(message.role + ": [Unsupported content type]")

        # Check if an image file is available
        if hasattr(message.content[0], 'image_file'):
            new_file = messages.data[0].content[0].image_file.file_id

            # Download files created by assistant
            image_data = client.files.content(new_file)
            image_data_bytes = image_data.read()

            # Display images and files downloaded
            st.image(image_data_bytes)
        else:
            st.write('No image :(')
else:
    st.error("Please enter your OpenAI API Key in the sidebar.")


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

