import streamlit as st
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="chat_with_database",page_icon="books")
st.title("chat with database")



def init_database(host, port, user, password, database):
    db_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_uri)






with st.sidebar:
    st.subheader("Connection")
    host = st.text_input("Host",value="localhost")
    port = st.text_input("Port",value="3306")
    user = st.text_input("User",value="root")
    password = st.text_input("Password",type="password",value="admin")
    database = st.text_input("Database",value="test")

    if st.button("connect"):
        with st.spinner("connecting to the Database"):
            db = init_database(host=host,port=port,user=user,password=password,database=database)
            st.sesstion_state["Database"]=database
            st.success(f"Connected to {host}:{port}/{database}")


st.chat_input("Enter your message in here")


