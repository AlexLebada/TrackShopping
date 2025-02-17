from build_graph import app
import streamlit as st
import datetime, langchain, logging, os
from agents import reasoning_llm
from langchain_community.callbacks.manager import get_openai_callback
from PIL import Image

langchain.debug = True


# RUN GRAPH
current_date = datetime.datetime.now()
filename = "./results/answer_%s%s%s_%s%s.txt"%(current_date.year,current_date.strftime("%m"),current_date.strftime("%d"),current_date.hour, current_date.minute )

query = "As an example, you have as input an image of a receipt. How would you store into database the main elements of this receipt"

def run_graph():
    with get_openai_callback() as cb:
        with open(filename, "w", encoding="utf-8") as file:
            for step in app.stream(
                {"input": query,
                 "plan": ""},
                {"recursion_limit": 10},
                #stream_mode="values"
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
                f"Query:{query}"
                f"Reasoning model:{reasoning_llm}"
            )
            print(token_info)
            file.write(token_info)






def main():
    st.title("Test")
    st.write("Username: Giovanni Giorgio")
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        # To read file as bytes:
        #bytes_data = uploaded_file.getvalue()
        #st.write("Original:",bytes_data)
        # display image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        # Define file path to save
        file_path = os.path.join("./user_input/raw", uploaded_file.name)

        # Save file to the folder
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())





if __name__ == "__main__":
    #main()
    run_graph()