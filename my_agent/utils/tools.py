from langchain_core.messages import AIMessage
from langchain_core.tools import tool


@tool
def search_web(query: str):
    "Call to search the web with any query"
    print("Searching the web for:", query)
    results = "Agents are the future of programming!"
    return results


@tool
def calculate_math(expression: str):
    "Call to calculate math with any expression"
    print("Calculating math for:", expression)
    results = "The calculated answer is infinity!"
    return results


tools = [search_web, calculate_math]
