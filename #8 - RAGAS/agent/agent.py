import os
from typing import Annotated, Literal, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, BaseMessage, AIMessage
from langchain_core.tools import Tool
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from agent.tools import multiply, divide, sum, sub
from langchain.callbacks.tracers import LangChainTracer
from agent.states import StatusMessagesState
from langchain.schema import HumanMessage, SystemMessage, AIMessage

# For LangChain Community (newer versions):
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# For OpenAI-style messages:
from openai.types.chat import ChatCompletionMessage
from agent.prompts import SYSTEM_MESSAGE


def chatbot(state: StatusMessagesState):
    """Main chatbot node that processes user input and decides whether to use tools."""
    print("🤖 Chatbot node: Processing messages...")

    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-4.1",  # Using a more stable model
        temperature=0,
        max_tokens=1000
    )

    # Get user string from state or use default
    user_str = "default_user"
    try:
        if "user" in state:
            user_str = state["user"]
    except Exception as e:
        print(f"Error accessing user from state: {e}")
        
    # Clean up the messages to ensure proper structure
    # We need to make sure tool messages are always preceded by messages with tool_calls
    messages = state["messages"]

    # Create tools
    tools = [
        Tool(
            name="multiply", 
            func=multiply, 
            description="Multiplies two numbers. The arguments should be passed as 'a' and 'b'. The arguments should be __arg1 and __arg2. Each argument should be a number. It must always be two arguments (arg1 and arg2)."
        ),
        Tool(
            name="divide", 
            func=divide, 
            description="Divides two numbers. The arguments should be passed as 'a' and 'b'. The arguments should be __arg1 and __arg2. Each argument should be a number. It must always be two arguments (arg1 and arg2)."
        ),
        Tool(
            name="sum", 
            func=sum, 
            description="Sums two numbers. The arguments should be passed as 'a' and 'b'. The arguments should be __arg1 and __arg2. Each argument should be a number. It must always be two arguments (arg1 and arg2)."
        ),
        Tool(
            name="sub", 
            func=sub, 
            description="Subtracts two numbers. The arguments should be passed as 'a' and 'b'. The arguments should be __arg1 and __arg2. Each argument should be a number. It must always be two arguments (arg1 and arg2)."
        )
    ]

    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(tools)

    # Define the system message with user name
    system_message_content = SYSTEM_MESSAGE.replace("USER_NAME", user_str)

    print(f"System message content: {system_message_content}")
    # Add system message if not present
    messages = state["messages"]
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages = [SystemMessage(content=system_message_content)] + messages
    
    # Get response from LLM
    print(f"Messages: {messages}")
    response = llm_with_tools.invoke(messages)
    return {"messages": messages + [response]}


def should_continue(state: StatusMessagesState) -> Literal["tools", "__end__"]:
    """Determine whether to continue with tool calls or end."""
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, continue to tools node
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "node_tools"
    # Otherwise, end the conversation turn
    print("✅ Conversation complete")
    return "__end__"

def node_tools(state: StatusMessagesState):
    """Calls the tool based on the last message's tool call."""
    
    messages = state["messages"]
    last_message = messages[-1]
    
    # Keep track of all previous messages
    previous_messages = messages[:-1]  # All messages except the last one with tool calls
    
    print(f"Processing {len(last_message.tool_calls)} tool calls")
    
    # Create a list to store all tool messages
    tool_messages = []
    
    # Process all tool calls
    for tool in last_message.tool_calls:
        tool_call_id = tool['id']  # Get the tool call ID
        print(f"Processing tool call: {tool['name']}")
        print(tool)
        print('------------------')
        if tool['name'] == "multiply":
            a = tool['args']['__arg1']
            b = tool['args']['__arg2']
            result = multiply(a, b)
            tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
            
        elif tool['name'] == "divide":
            a = tool['args']['__arg1']
            b = tool['args']['__arg2']
            result = divide(a, b)
            tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
            
        elif tool['name'] == "sum":
            a = tool['args']['__arg1']
            b = tool['args']['__arg2']
            result = sum(a, b)
            tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
            
        elif tool['name'] == "sub":
            a = tool['args']['__arg1']
            b = tool['args']['__arg2']
            result = sub(a, b)
            tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))
    
    # Return all messages: previous messages + last message with tool calls + all tool messages
    return {
        "messages": previous_messages + [last_message] + tool_messages,
        "user": state.get("user", "default_user")
    }

def build_graph():
    
    # Define the graph
    workflow = StateGraph(StatusMessagesState)

    # Add nodes
    workflow.add_node("chatbot", chatbot)
    workflow.add_node("node_tools", node_tools)

    # Set entry point
    workflow.set_entry_point("chatbot")

    # Add conditional edges
    workflow.add_conditional_edges(
        "chatbot",
        should_continue,
        {"node_tools": "node_tools", "__end__": "__end__"}
    )

    # After tools, always go back to chatbot
    workflow.add_edge("node_tools", "chatbot")

    # Add memory for conversation history
    memory = MemorySaver()

    # Compile the graph
    app = workflow.compile(checkpointer=memory)
    return app

    

    