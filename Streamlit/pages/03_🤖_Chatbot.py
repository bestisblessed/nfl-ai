import streamlit as st
import openai
from openai import OpenAI
import os
import requests
import time
from dotenv import load_dotenv
from IPython.display import Image

load_dotenv()
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
client = OpenAI(api_key=OPEN_AI_API_KEY)

# assistant_football_buddy = 'asst_bus6Qg0cy62xe7IhbndWXnXB'
assistant_football_buddy_GPT_3_Turbo = 'asst_dF6eUKIKhbtmSVUcKAXy6y8v'
assistant = client.beta.assistants.retrieve(assistant_football_buddy_GPT_3_Turbo)

st.title('NFL Chatbot')

### --- CHAT ---- ###

user_question = st.text_input("Enter your question:", "")

# # Advanced feature display stats if name is in the users question
# player_name = "Dak Prescott"  # Example, can be dynamically set based on user input
# if player_name == "Dak Prescott":
#     st.write("Showing stats for Dak Prescott...")
#     # Code to display Dak Prescott's stats

if user_question:

    # Create thread
    thread = client.beta.threads.create()
    st.write('Thread Info: ', thread)

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_question,
    )

    # Run it 
    run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
    )

    # st.write('Processing..')
    processing_message = st.empty()
    # processing_message.write('Processing...')
    # loading_symbol = st.spinner('Processing...')
    # processing_message.write('Processing...')

    with st.spinner('Processing...'):
        # Wait for completion 
        while run.status != "completed":
            time.sleep(2)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            # st.write(run.status)

    # Remove or update the processing message
    # processing_message.write('Done!')
    st.success('Done!')

    # Display assistant response
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )
    # st.write('messages: ', messages)

    # Print last message
    st.write('Last Message: ', messages.data[0].content[0])

    # Print all messages
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
        # Print and get any new files file_id
        new_file = messages.data[0].content[0].image_file.file_id
        # st.write(new_file)

        # Download files created by assistant
        image_data = client.files.content(new_file)
        image_data_bytes = image_data.read()

        # Display images and files downloaded
        # st.write(image_data_bytes)
        st.image(image_data_bytes)
        # with open("./my-image.png", "wb") as file:
        #     file.write(image_data_bytes)
        #     Image(filename="./my-image.png")
    else:
        st.write('No image :(')
    # # Check if an image file is available
    # if 'image_file' in messages.data[0].content[0]:
    #     new_file = messages.data[0].content[0].image_file.file_id
    #     st.write(new_file)

    #     # Download files created by assistant
    #     image_data = client.files.content(new_file)
    #     image_data_bytes = image_data.read()

    #     # Display images and files downloaded
    #     with open("./my-image.png", "wb") as file:
    #         file.write(image_data_bytes)
    #         Image(filename="./my-image.png")
    # else:
    #     st.write("No image was generated.")

