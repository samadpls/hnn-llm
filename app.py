PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION = 'python'
import os
import time
import streamlit as st
from streamlit import secrets
from prompt import *
from langchain.docstore.document import Document
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma


class HNNChatbot:
    def __init__(self):
        self.groq_api_key = "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"
        self.llm = ChatGroq(groq_api_key=self.groq_api_key,
                            model_name="Llama3-8b-8192")
        self.prompt = ChatPromptTemplate.from_template(
            """
            Answer the questions based on the provided context only.
            Please provide the most accurate response based on the question.
            Response Format: Your response must be in markdown format.

            {context}

            Question: {input}
            """
        )
        self.vectorstore = self.initialize_vectorstore()

    def initialize_vectorstore(self):
        embeddings = HuggingFaceBgeEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        files = ["hnn_core_data.txt",
                 "hnn_example_tutorials.txt", "hnn_website_data.txt"]
        documents = [
            doc for file in files for doc in self.load_documents(file)]

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200)
        final_documents = text_splitter.split_documents(documents)

        vectorstore = Chroma.from_documents(
            documents=final_documents,
            embedding=embeddings,
            persist_directory="/tmp/.chroma",
            collection_name="documents_collection"
        )

        return vectorstore

    def load_documents(self, file):
        try:
            loader = TextLoader(f"./data/{file}")
            return loader.load()
        except Exception:
            return []

    def query_documents(self, input_prompt):
        retrieval_chain = self.create_retrieval_chain()

        start = time.process_time()
        response = retrieval_chain.invoke({'input': input_prompt})
        response_time = time.process_time() - start

        top_chunks = response.get('context', [])
        formatted_chunks = [doc.page_content.strip() for doc in top_chunks[:3]]

        refined_response = self.refine_response(input_prompt, formatted_chunks)
        return refined_response, response_time

    def create_retrieval_chain(self):
        retriever = self.vectorstore.as_retriever()
        document_chain = create_stuff_documents_chain(self.llm, self.prompt)
        return create_retrieval_chain(retriever, document_chain)

    def refine_response(self, input_prompt, chunks):
        refined_prompt = ChatPromptTemplate.from_template(
            HNN_DOCUMENTATION_PROMPT
        )
        refined_chain = create_stuff_documents_chain(self.llm, refined_prompt)
        refined_response = refined_chain.invoke({
            'input': input_prompt,
            'context': [Document(page_content=chunk) for chunk in chunks]
        })
        return refined_response


def main():
    st.title("HNN-LLM:\n #### Knowledge Retrieval System for HNN Documentation")

    chatbot = HNNChatbot()

    if 'vectorstore' not in st.session_state:
        st.session_state.vectorstore = chatbot.vectorstore

    user_input = st.text_input("Enter your question:")
    st.markdown("Made with 🤍 by `samadpls`")
    if user_input:
        with st.spinner("Querying documents..."):
            answer, response_time = chatbot.query_documents(user_input)
            st.markdown(answer)
            st.info(f"Response time: {response_time:.2f} seconds")


if __name__ == "__main__":
    main()
