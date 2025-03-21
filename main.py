
import asyncio
import streamlit as st
import uuid
import re
from src.model import AirlineAgentContext
from src.agent_def import triage_agent
from agents import Runner, ItemHelpers, trace, set_tracing_disabled
from openai import APITimeoutError
# from langsmith.wrappers import OpenAIAgentsTracingProcessor

# Initialize Streamlit app
st.title("Airline Agent Chatbot")
st.write("Type your message below and interact with the AI assistant.")

# Session state for conversation tracking
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = uuid.uuid4().hex[:16]
    st.session_state.messages = []
    st.session_state.current_agent = triage_agent
    st.session_state.context = AirlineAgentContext()

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

async def main():
    # Chat input box
    user_input = st.chat_input("Enter your message")

    if user_input:
        st.session_state.messages.append({"content": user_input, "role": "user"})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with trace('FlightAgent'):
            result = Runner.run_streamed(
                st.session_state.current_agent,
                st.session_state.messages,
                context=st.session_state.context,
            )
            
            response_text = "Typing"
            # Placeholder for assistant response
            # Show "typing..." indicator
            with st.chat_message("assistant"):
                typing_placeholder = st.empty()
                typing_placeholder.markdown(f"_{response_text}_")

            try:

                async for event in result.stream_events():
                    if event.type == "raw_response_event":
                        continue
                    elif event.type == "agent_updated_stream_event":
                        st.session_state.current_agent = event.new_agent
                        continue
                    elif event.type == "run_item_stream_event":
                        if event.item.type == "tool_call_item":
                            response_text = "-- Tool was called"
                        elif event.item.type == "tool_call_output_item":
                            response_text = f"🔴 Tool output: {event.item.output}"
                        elif event.item.type == "handoff_output_item":
                            response_text = f"🟡 Handoff '{event.item.source_agent.name}' -> '{event.item.target_agent.name}'"
                        elif event.item.type == "message_output_item":
                            response_text = re.sub(r'<think>.*?</think>\s*', '', ItemHelpers.text_message_output(event.item), flags=re.DOTALL)
                        typing_placeholder.markdown(response_text)
            except APITimeoutError:
                response_text = "Unable to reach AI"

            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.session_state.current_agent = result.last_agent
        
        
if __name__ == "__main__":
    # set_trace_processors([OpenAIAgentsTracingProcessor()])
    # set_tracing_disabled(True)
    asyncio.run(main())