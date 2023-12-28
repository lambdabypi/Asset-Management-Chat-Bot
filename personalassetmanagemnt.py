import streamlit as st
from streamlit_chat import message
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import Replicate
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import os
from dotenv import load_dotenv
import mysql.connector

# Set your Replicate API token and MySQL database credentials
os.environ["REPLICATE_API_TOKEN"] = "r8_2YlFz7LtuNHULMYRVyW7P30ePqu1a7X2A3dJA"
load_dotenv()

def initialize_session_state():
    if 'history' not in st.session_state:
        st.session_state['history'] = []

    if 'generated' not in st.session_state:
        st.session_state['generated'] = ["Hello! Ask me anything about your assets."]

    if 'past' not in st.session_state:
        st.session_state['past'] = ["Hey! 👋"]

def get_asset_info(asset_type, db_cursor):
    query = f"SELECT p.name, a.asset_type, , a.asset_count, a.asset_value FROM assets a join people p on a.person_id = p.id having a.asset_type = %s;"
    db_cursor.execute(query, (asset_type,))
    
    results = db_cursor.fetchall()
    
    # Get the column names
    column_names = [desc[0] for desc in db_cursor.description]

    # Create a dictionary with column names as keys
    results_list = [dict(zip(column_names, row)) for row in results]

    return results_list

def get_all_asset_info(db_cursor):
    query = f"SELECT p.name, a.asset_type, a.asset_count, a.asset_value FROM assets a join people p on a.person_id = p.id;"
    db_cursor.execute(query)
                        
    results = db_cursor.fetchall()
                        
    # Get the column names
    column_names = [desc[0] for desc in db_cursor.description]

    # Create a dictionary with column names as keys
    results_list = [dict(zip(column_names, row)) for row in results]

    return results_list

def get_user_info(db_cursor):
    query = f"SELECT * FROM people;"
    db_cursor.execute(query)
                        
    results = db_cursor.fetchall()
                        
    # Get the column names
    column_names = [desc[0] for desc in db_cursor.description]

    # Create a dictionary with column names as keys
    results_list = [dict(zip(column_names, row)) for row in results]

    return results_list


def conversation_chat(query, chain, history, db_cursor):    
    asset_types = ["Real Estate", "Stocks", "Vehicles", "Jewelry", "Cash", "Laptops", "Mobiles"]
    
    response = None  # Initialize response variable
    
    asset_types = ["Real Estate", "Stocks", "Vehicles", "Jewelry", "Cash", "Laptops", "Mobiles"]
    for asset_type in asset_types:
        if asset_type.lower() in query.lower() or query.lower() in asset_type.lower():
            asset_info = get_asset_info(asset_type, db_cursor)
            if asset_info:
                response = f"You're {asset_type} information is:\n"
                break  # Exit the loop once a match is found
            else:
                response = "Not sure what you're asking. Try again"
        if "asset information" in query.lower():
            response = f"This is all the available asset information:\n"
        if "user information" in query.lower():
            response = f"This is all the available user information:\n"

    if response is None:
        # If no asset information found, use the conversational model
        result = chain({"question": query, "chat_history": history})
        response = result["answer"]
    
    history.append((query, response))
    return response

def display_chat_history(chain, db_cursor):
    reply_container = st.container()
    container = st.container()

    with container:
        with st.form(key=f'my_form_', clear_on_submit=True):  # Append user_input to the key
            user_input = st.text_input("Question:", placeholder="Ask about your assets", key=f'input_')
            submit_button = st.form_submit_button(label='Send')

        if submit_button and user_input:
            with st.spinner('Generating response...'):
                output = conversation_chat(user_input, chain, st.session_state['history'], db_cursor)
    
            st.session_state['past'].append(user_input)
            st.session_state['generated'].append(output)

    if st.session_state['generated']:
        with reply_container:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
                message(st.session_state["generated"][i], key=str(i))
                asset_types = ["Real Estate", "Stocks", "Vehicles", "Jewelry", "Cash", "Laptops", "Mobiles"]
                for asset_type in asset_types:
                    if asset_type.lower() in st.session_state["past"][i].lower():
                        asset_info = get_asset_info(asset_type, db_cursor)
                        if asset_info:
                            info =  asset_info
                            st.table(info)
                if "asset information" in st.session_state["past"][i].lower():
                    info =  get_all_asset_info(db_cursor)
                    st.table(info)
                if "user information" in st.session_state["past"][i].lower():
                    info =  get_user_info(db_cursor)
                    st.table(info)

def create_conversational_chain(vector_store):
    load_dotenv()
    llm = Replicate(
        streaming=True,
        model="replicate/llama-2-70b-chat:58d078176e02c219e11eb4da5a02a7830a283b14cf8f94537af893ccff5ee781",
        callbacks=[StreamingStdOutCallbackHandler()],
        input={"temperature": 0.01, "max_length": 500, "top_p": 1}
    )
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    chain = ConversationalRetrievalChain.from_llm(llm=llm, chain_type='stuff',
                                                 retriever=vector_store.as_retriever(search_kwargs={"k": 2}),
                                                 memory=memory)
    return chain

class Document:
    def __init__(self, page_content, metadata={}):
        self.page_content = page_content
        self.metadata = metadata

def main():
    load_dotenv()
    initialize_session_state()
    # Set the theme
    st.set_page_config(page_title="Asset ChatBot 💰", layout="centered")

    st.title("Asset ChatBot 💰")

    with mysql.connector.connect(
        host='localhost',
        user='root',
        password='DBMS*fall2023',
        database='assets'
    ) as db:
        with db.cursor() as db_cursor:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'})

            texts = [Document("Document 1 text"), Document("Document 2 text"), Document("Document 3 text")]

            vector_store = FAISS.from_documents(texts, embedding=embeddings)

            chain = create_conversational_chain(vector_store)
            display_chat_history(chain, db_cursor)

if __name__ == "__main__":
    main()