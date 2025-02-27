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


@tool
def get_weather_forecast(city: str):
    "Call to get a weather forecast for a given city"
    print("Getting weather forecast for:", city)
    forecast = f"The weather in {city} is sunny with a high of 25°C."
    return forecast


@tool
def translate_text(text: str):
    "Call to translate text from English to Spanish"
    print("Translating text:", text)
    translation = "El texto traducido es: ¡Hola, mundo!"
    return translation


tools = [search_web, calculate_math]
