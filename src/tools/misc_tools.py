from datetime import datetime
from langchain.tools import tool

@tool
def current_date() -> str:
    """Tool to get the current date in format YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")
