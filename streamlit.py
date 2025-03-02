import streamlit as st
import os
import re
import json
from nanoengineer import NanoEngineer, LLMInteract
from tools import WeatherTool, HotelTool, SightseeingTool, MapSearchTool, WikiTool
from streamlit_widgets import MapWidget, MetricWidget
import logging as lg
from dotenv import load_dotenv

load_dotenv()

lg.basicConfig(level=lg.INFO)
st.set_page_config(page_title="Travel Assistant")


if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'nano' not in st.session_state:
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    language_model = os.getenv("LANGUAGE_MODEL")
    language_provider = os.getenv("LANGUAGE_PROVIDER")
    lg.info(f"Using language model {language_model} by {language_provider}")

    llm = LLMInteract(provider=language_provider,
                      model=language_model,
                      api_key=anthropic_key)

    nano = NanoEngineer(llm)

    nano.register_tools([
        WeatherTool,
        HotelTool,
        SightseeingTool,
        MapSearchTool,
        WikiTool
    ])

    nano.register_widgets([
        MapWidget,
        MetricWidget
    ])

    st.session_state.nano = nano


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            ask_pattern = r'<Ask.*?>(.*?)</Ask>'
            message_pattern = r'<Message.*?>(.*?)</Message>'
            answer_pattern = r'<Answer.*?>(.*?)</Answer>'
            
            display_content = []
            
            for pattern in [ask_pattern, message_pattern, answer_pattern]:
                matches = re.findall(pattern, message["content"], re.DOTALL)
                display_content.extend(matches)

                
            if display_content:
                st.markdown('\n\n'.join(display_content))
            else:
                st.markdown(message["content"])
                
        else:
            st.write(message["content"])

if prompt := st.chat_input("What would you like to know about travel?"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        full_response = ""
        status_messages = []
        
        with st.status("Processing...", expanded=False) as status:
            for chunk in st.session_state.nano.send_message(prompt, yield_response=True):
                if isinstance(chunk, list):
                    for i, step in enumerate(chunk):
                        status_msg = f"Step {i+1}: {step}"
                        status.update(label=status_msg)
                        status.write(status_msg)
                        status_messages.append(status_msg)
                elif isinstance(chunk, dict):
                    status_msg = f"Checking information using {chunk.get('content', {}).get('execute_tool', 'tool')}..."
                    status.update(label=status_msg)
                    status.write(status_msg)
                    status_messages.append(status_msg)
                else:
                    full_response += chunk
                
            status.update(label="Complete!", state="complete")
        
        message_placeholder = st.empty()
        ask_pattern = r'<Ask.*?>(.*?)</Ask>'
        message_pattern = r'<Message.*?>(.*?)</Message>'

        if st.session_state.nano.answer_instruction is not None:
            answer_pattern = r'<FormattedAnswer.*?>(.*?)</FormattedAnswer>'
        else:
            answer_pattern = r'<Answer.*?>(.*?)</Answer>'
        
        display_content = []
        
        for pattern in [ask_pattern, message_pattern]:
            matches = re.findall(pattern, full_response, re.DOTALL)
            display_content.extend(matches)

        widgets = re.findall(
            r'<Widget plan=\d+ name="([^"]+)">(.*?)</Widget>',
            full_response, 
            re.DOTALL
        )

        # Filter out widget tags from the full response
        full_response = re.sub(
            r'<Widget plan=\d+ name="[^"]+">(.*?)</Widget>',
            '',
            full_response,
            flags=re.DOTALL
        )

        answer_matches = re.findall(answer_pattern, full_response, re.DOTALL)
        display_content.extend(answer_matches)
        
        for widget_name, widget_content in widgets:
            try:
                widget_params = json.loads(widget_content)
            except:
                st.write(widget_content)
                st.error(f"Error parsing widget params: {widget_content}")
                continue

            match widget_name:
                case "map":
                    map_widget = MapWidget()
                    map_widget.display(widget_params)
                case "metric":
                    metric_widget = MetricWidget()
                    metric_widget.display(widget_params)
        
        if display_content:
            message_placeholder.markdown('\n\n'.join(display_content))
        else:
            message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({
        "role": "assistant", 
        "content": full_response,
        "status": status_messages
    })
