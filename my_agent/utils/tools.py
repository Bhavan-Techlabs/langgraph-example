from langchain_core.messages import AIMessage
from langchain_core.tools import tool


@tool
def search_web(query: str):
    "Call to search the web with any query"
    print("Searching the web for:", query)
    results = "This is a test of search_web"
    return results


@tool
def calculate_math(expression: str):
    "Call to calculate math with any expression"
    print("Calculating math for:", expression)
    results = "The calculated answer is 42"
    return results


tools = [search_web, calculate_math]
