import streamlit as st
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv
from langchain_core.messages import AIMessage,HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms import HuggingFaceEndpoint

load_dotenv()
st.set_page_config(page_title="chat_with_database",page_icon="books")
st.title("chat with database")



def init_database(host, port, user, password, database):
    db_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_uri)


def get_sql_chain(db):
  template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, write a SQL query that would answer the user's question. Take the conversation history into account.
    
    <SCHEMA>{schema}</SCHEMA>
    
    Conversation History: {chat_history}
    
    Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.
    
    For example:
    Question: which 3 artists have the most tracks?
    SQL Query: SELECT ArtistId, COUNT(*) as track_count FROM Track GROUP BY ArtistId ORDER BY track_count DESC LIMIT 3;
    Question: Name 10 artists
    SQL Query: SELECT Name FROM Artist LIMIT 10;
    
    Your turn:
    
    Question: {question}
    SQL Query:
    """
    
  prompt = ChatPromptTemplate.from_template(template)
  
  #llm = Ollama(model="llama3")
  llm = HuggingFaceEndpoint(repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1", max_length=128, temperature=0.1,verbose = True)
  
  def get_schema(_):
    return db.get_table_info()
  
  return (
    RunnablePassthrough.assign(schema=get_schema)
    | prompt
    | llm
    | StrOutputParser()
  )


def get_response(question,db,chat_history):
    sql_chain = get_sql_chain(db)
    template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, question, sql query, and sql response, write a natural language response.
    <SCHEMA>{schema}</SCHEMA>

    Conversation History: {chat_history}
    SQL Query: <SQL>{query}</SQL>
    User question: {question}
    SQL Response: {response}
    """
  
    prompt = ChatPromptTemplate.from_template(template)
    
    llm = HuggingFaceEndpoint(repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1", max_length=128, temperature=0.1,verbose = True)
    #llm = Ollama(model="mistral")

    chain = (RunnablePassthrough.assign(query=sql_chain).assign(
        schema=lambda _: db.get_table_info(),
        response=lambda vars: db.run(vars["query"]),
    )
    | prompt
    | llm
    | StrOutputParser()
    )

    return chain.invoke({
        "question": question,
        "chat_history": chat_history})



  
    





if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Hello, I am a SQL assistant. Ask me anything related to the database.")
    ]




with st.sidebar:
    st.subheader("Connection")
    st.text_input("Host",value="localhost",key="Host")
    st.text_input("Port",value="3307",key="Port")
    st.text_input("User",value="root",key="User")
    st.text_input("Password",type="password",value="root",key="Password")
    st.text_input("Database",value="employee_db",key="Database")

    if st.button("connect"):
        with st.spinner("connecting to the Database"):
            st.session_state.db = init_database(st.session_state["Host"],st.session_state["Port"],st.session_state["User"],st.session_state["Password"],st.session_state["Database"])
            st.success(f"Connected to the Database")




user_query = st.chat_input("Enter your message in here")

if user_query is not None and user_query.strip() != "":
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    
    response =get_response(user_query,st.session_state.db,st.session_state.chat_history)

    st.session_state.chat_history.append(AIMessage(content=response))





for message in st.session_state.chat_history:
    if isinstance(message,AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    else:
        with st.chat_message("Human"):
            st.markdown(message.content)
