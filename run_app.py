from build_graph import app
import streamlit as st
import datetime, langchain, logging, os, json
from agents import reasoning_llm
from langchain_community.callbacks.manager import get_openai_callback
from UI_modules import display_values
from results.queries.queries import queries
from st_multimodal_chatinput import multimodal_chatinput
from langgraph.errors import GraphRecursionError
from UI_modules import load_css
from utils import get_mongo_db, files_rename_store

langchain.debug = True


# RUN GRAPH
current_date = datetime.datetime.now()
filename = "./results/answer_%s%s%s_%s%s.txt"%(current_date.year,current_date.strftime("%m"),current_date.strftime("%d"),current_date.hour, current_date.minute )

query = queries[14]

def run_graph():
    with get_openai_callback() as cb:
        with open(filename, "w", encoding="utf-8") as file:
            try:
                for step in app.stream(
                        {"input": query,
                         "plan": "",
                         "query_response": f"{filename}"},
                        {"recursion_limit": 20},
                        # stream_mode="values"
                ):
                    print(step)
                    print("----")
                    file.write(str(step))
                    file.write("\n----\n")

                token_info = (
                    f"Total Tokens: {cb.total_tokens}\n"
                    f"Prompt Tokens: {cb.prompt_tokens}\n"
                    f"Completion Tokens: {cb.completion_tokens}\n"
                    f"Total Cost (USD): ${cb.total_cost}\n"
                    f"Query:{query}\n"
                    f"Reasoning model:{reasoning_llm}\n"
                )
                print(token_info)
                file.write(token_info)
            except GraphRecursionError:
                db = get_mongo_db()
                data = {
                    "query": query,
                    "results": f"{filename}",
                    "error_type": "RECURSION_LIMIT",
                    "status": "waiting"
                }
                db_returned = db["user_request_issues"].insert_one(data)




#
def main():
    st.set_page_config(layout="wide")
    #load_css("./frontend/style.css")
    col1, col2, col3 = st.columns([1, 3, 1])
    # to display requested values for monitoring
    with col1:
        st.header("User Information")
        #display_values()

    with col2:
        if "messages" not in st.session_state.keys():
            st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
        st.title("Test")
        st.write("Username: Giovanni Giorgio")
        #prompt = st.text_area(label="", height=250)
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if "last_input" not in st.session_state:
            st.session_state.last_input = ""

       # text = st.chat_input("Type your message...")
        text = st.text_input("asd",placeholder="Type your message...", label_visibility="hidden")

        if text and text != st.session_state.last_input:
            st.session_state.last_input = text  # Update stored input

        uploaded_file = st.file_uploader("Choose a file", accept_multiple_files=True)
        files = []
        if st.button("➡️ Submit"):
            if uploaded_file is not None:
                filenames = files_rename_store(uploaded_file)
                # upload_prompt = f"Store these files: {filenames}"

            #st.rerun()

# access user's files
    with col3:

        # Base folder path
        base_folder = "./user_input/raw/"

        # Session state to track current directory
        if "current_folder" not in st.session_state:
            st.session_state.current_folder = base_folder

        # Get the current folder
        current_folder = st.session_state.current_folder

        # Get list of folders and files
        items = os.listdir(current_folder)
        folders = [f for f in items if os.path.isdir(os.path.join(current_folder, f))]
        files = [f for f in items if os.path.isfile(os.path.join(current_folder, f))]

        # Navigation: Go back button
        if current_folder != base_folder:
            if st.button("⬅️ Back"):
                st.session_state.current_folder = os.path.dirname(current_folder)
                st.rerun()

        st.write(f"📂 Browsing: {current_folder}")

        # Display folders as navigation buttons
        for folder in folders:
            if st.button(f"📁 {folder}"):
                st.session_state.current_folder = os.path.join(current_folder, folder)
                st.rerun()

        # Display files with download buttons
        if not files and not folders:
            st.warning("No files or folders found.")
        else:
            for file in files:
                file_path = os.path.join(current_folder, file)

                with open(file_path, "rb") as f:
                    st.download_button(label=f"📄 {file}",
                                       data=f,
                                       file_name=file,
                                       mime="application/octet-stream")




if __name__ == "__main__":
    main()
    #run_graph()