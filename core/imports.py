# core/imports.py
import os
import random
from dotenv import load_dotenv
from typing import TypedDict
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
