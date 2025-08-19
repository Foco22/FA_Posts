import os
from typing import Annotated, Literal, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import Tool
from langgraph.graph import StateGraph, MessagesState
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# --- 2. TOOL FUNCTIONS ---
def multiply(a: int, b: int) -> int:
    """Multiplies two numbers.
    
    Args:
        a (int): The first number.
        b (int): The second number.
    
    Returns:
        int: The product of the two numbers.
    """
    print(f"🔍 Calling Tool: multiply(a={a}, b={b})")
    a = float(a)
    b = float(b)
    return a * b

def divide(a: int, b: int) -> float:
    """Divides two numbers.
    
    Args:
        a (int): The numerator.
        b (int): The denominator.
    
    Returns:
        float: The quotient of the division.
    """
    print(f"🔍 Calling Tool: divide(a={a}, b={b})")
    a = float(a)
    b = float(b)
    return a / b

def sum(a: int, b: int) -> int:
    """Sums two numbers.
    
    Args:
        a (int): The first number.
        b (int): The second number.
    
    Returns:
        int: The sum of the two numbers.
    """
    print(f"🔍 Calling Tool: sum(a={a}, b={b})")
    a = float(a)
    b = float(b)
    return a + b
    
def sub(a: int, b: int) -> int:
    """Subtracts two numbers.
    
    Args:
        a (int): The first number.
        b (int): The second number.
    
    Returns:
        int: The difference of the two numbers.
    """
    print(f"🔍 Calling Tool: sub(a={a}, b={b})")
    a = float(a)
    b = float(b)
    return a - b
    