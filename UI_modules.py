import json
import streamlit as st
from generated_functions.schedule_write import write_values




def display_values():
      results = write_values()
      print(results)
      with open("./generated_functions/display.json", 'r') as file:
            data = json.load(file)

      for field in data.values():
            if field["display"] == True:
                  st.write(field["name"])
                  st.write(field["value"])


def load_css(css_file):
    with open(css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


