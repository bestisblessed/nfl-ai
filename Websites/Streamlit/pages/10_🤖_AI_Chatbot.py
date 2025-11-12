# streamlit_app_assistants_full.py
import streamlit as st
from openai import OpenAI
import time
from PIL import Image
import io
import pandas as pd
import os
from utils.footer import render_footer

st.title("NFL AI Chatbot")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ---- Create Assistant (with file upload) ----
if "assistant_id" not in st.session_state:
    # Upload CSVs when creating assistant
    uploaded = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, '../data')

    for filename in ["player_stats_pfr.csv", "all_team_game_logs.csv", "Rosters.csv"]:
        filepath = os.path.join(data_dir, filename)
        with open(filepath, "rb") as f:
            uploaded.append(client.files.create(file=f, purpose="assistants"))
    st.session_state.file_ids = [f.id for f in uploaded]

    # Create assistant with uploaded files
    assistant = client.beta.assistants.create(
        name="NFL AI Chatbot",
        # model="gpt-4o-mini",
        model="gpt-4.1-nano",
        tools=[{"type": "code_interpreter"}],
        tool_resources={
            "code_interpreter": {
                "file_ids": st.session_state.file_ids
            }
        },
        instructions="""You are an NFL data analyst with access to CSV files. You MUST use the code interpreter to read and analyze these files.

CRITICAL: When creating visualizations, you MUST:
1. Use matplotlib or seaborn to create plots
2. Save plots using plt.savefig('plot.png') or fig.savefig('plot.png')
3. For data analysis, save results as CSV using df.to_csv('results.csv')

Available files to read:
- pd.read_csv('player_stats_pfr.csv') - Player statistics
- pd.read_csv('all_team_game_logs.csv') - Team performance by game
- pd.read_csv('Rosters.csv') - Player biographical information

ALWAYS create actual visualizations and save them as files. Show specific data analysis with real numbers."""
    )
    st.session_state.assistant_id = assistant.id

# ---- Chat History ----
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---- Helper: run a prompt through the assistant ----
def run_query(prompt: str):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Create thread and run
    thread = client.beta.threads.create(messages=[{"role": "user", "content": prompt}])
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=st.session_state.assistant_id
    )

    # Poll until completion
    while run.status not in ("completed", "failed", "cancelled"):
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Retrieve messages (final model response)
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    assistant_message = messages.data[0]

    # Handle different content types (text and images)
    text_parts = []
    displayed_file_ids = set()
    with st.chat_message("assistant"):
        for content_block in assistant_message.content:
            # Text blocks
            if hasattr(content_block, "text") and content_block.text:
                text_value = content_block.text.value
                st.markdown(text_value)
                text_parts.append(text_value)

            # Inline image blocks (show inside the assistant message)
            elif hasattr(content_block, "image_file") and content_block.image_file:
                file_id = getattr(content_block.image_file, "file_id", None) or getattr(
                    content_block.image_file, "id", None
                )
                if file_id:
                    try:
                        file_data = client.files.content(file_id).read()
                        file_obj = client.files.retrieve(file_id)
                        file_name = getattr(file_obj, "filename", "") or "generated_image"
                        image = Image.open(io.BytesIO(file_data))
                        st.image(image, caption=file_name)
                        displayed_file_ids.add(file_id)
                    except Exception:
                        pass

    # Combine all text parts for session storage
    text_output = "\n".join(text_parts)
    st.session_state.messages.append({"role": "assistant", "content": text_output})

    # ---- Handle Generated Files (images, tables, etc.) ----
    steps = client.beta.threads.runs.steps.list(thread_id=thread.id, run_id=run.id)
    # st.write(f"Debug: Found {len(steps.data)} steps")

    for step in steps.data:
        if not hasattr(step, "step_details"):
            continue
        details = step.step_details
        # st.write(f"Debug: Step type: {getattr(details, 'type', 'unknown')}")

        if hasattr(details, "tool_outputs"):
            # st.write(f"Debug: Found {len(details.tool_outputs)} tool outputs")
            for output in details.tool_outputs:
                # st.write(f"Debug: Output type: {output.get('type', 'unknown')}")
                if output["type"] == "file":
                    file_id = output["file_id"]
                    # st.write(f"Debug: Processing file_id: {file_id}")
                    # Skip files already displayed inline from content blocks
                    if file_id in displayed_file_ids:
                        # st.write(f"Debug: Skipping already displayed file: {file_id}")
                        continue

                    try:
                        file_obj = client.files.retrieve(file_id)
                        file_name = getattr(file_obj, "filename", "")
                        # st.write(f"Debug: Retrieved file: {file_name}")

                        file_data = client.files.content(file_id).read()
                        file_ext = file_name.split(".")[-1].lower() if file_name else ""
                        # st.write(f"Debug: File extension: {file_ext}")

                        # ---- Display images ----
                        if file_ext in ["png", "jpg", "jpeg"]:
                            image = Image.open(io.BytesIO(file_data))
                            st.image(image, caption=file_name or "Generated plot")
                            # st.write("Debug: Displayed image successfully")

                        # ---- Display CSVs or TSVs ----
                        elif file_ext in ["csv", "tsv"]:
                            try:
                                sep = "," if file_ext == "csv" else "\t"
                                df = pd.read_csv(io.BytesIO(file_data), sep=sep)
                                st.dataframe(df.head(20))
                                # st.write("Debug: Displayed CSV successfully")
                            except Exception as e:
                                st.warning(f"Error reading table file {file_name}: {e}")

                        # ---- Display text or JSON ----
                        elif file_ext in ["txt", "json"]:
                            try:
                                text = file_data.decode("utf-8")
                                st.text_area(file_name or "Text Output", text, height=200)
                                # st.write("Debug: Displayed text successfully")
                            except Exception:
                                st.write("⚠️ Could not decode text output.")

                    except Exception as e:
                        # st.write(f"Debug: Error processing file {file_id}: {e}")
                        pass


# ---- Sample questions UI ----
with st.sidebar:
    st.write("### Sample Questions")
    if st.button('Tell me about your datasets', use_container_width=True):
        st.session_state.pending_query = "Tell me about your datasets"
    if st.button('Analyze datasets for handicapper trends', use_container_width=True):
        st.session_state.pending_query = "Analyze your datasets and find and visualize a few different useful trends for a handicapper"
    if st.button('Create visualizations for key metrics', use_container_width=True):
        st.session_state.pending_query = "Create visualizations for key NFL metrics like team performance, player stats, and scoring trends"

# ---- Handle pending query from sidebar buttons ----
if "pending_query" in st.session_state and st.session_state.pending_query:
    query = st.session_state.pending_query
    st.session_state.pending_query = None  # Clear it
    run_query(query)

# ---- Handle User Prompt ----
if prompt := st.chat_input("Question?"):
    run_query(prompt)

# Footer
render_footer()
