"""Orchestation script for math_coding agent."""
import json
import os
import time
from dotenv import load_dotenv
from typing import Any, Dict, List
from azure.ai.inference.prompts import PromptTemplate
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import CodeInterpreterTool
from azure.ai.projects import AIProjectClient

from opentelemetry import trace
from azure.monitor.opentelemetry import configure_azure_monitor

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(), conn_str=os.environ["CONNECTION_STRING"]
)

# Enable Azure Monitor tracing
application_insights_connection_string = project_client.telemetry.get_connection_string()

if not application_insights_connection_string:
    print("Application Insights was not enabled for this project.")
    print("Enable it via the 'Tracing' tab in your AI Foundry project page.")
    exit()

configure_azure_monitor(connection_string=application_insights_connection_string)

scenario = os.path.basename(__file__)
tracer = trace.get_tracer(__name__)


def simplify_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplify a message dictionary by flattening nested structures and removing empty fields.

    Args:
        msg: Dictionary containing message data with potentially nested structures

    Returns:
        Dictionary with flattened structure suitable for JSON serialization
    """
    # Create a new dict with basic fields
    simplified = {
        'id': msg.get('id'),
        'object': msg.get('object'),
        'created_at': str(msg.get('created_at')),
        'assistant_id': msg.get('assistant_id', ""),
        'thread_id': msg.get('thread_id'),
        'run_id': msg.get('run_id'),
        'role': msg.get('role'),
    }

    # Extract content text from nested structure
    content = msg.get('content', [])
    if content and isinstance(content, list) and len(content) > 0:
        text_content = content[0].get('text', {})
        simplified['content_text'] = text_content.get('value', '')
    else:
        simplified['content_text'] = ''

    # Remove None values
    simplified = {k: v for k, v in simplified.items() if v is not None}

    return simplified


def convert_and_serialize(data: List[Dict[str, Any]]) -> str:
    """
    Convert a list of message dictionaries to a simplified format and serialize to JSON.

    Args:
        data: List of message dictionaries

    Returns:
        JSON string of simplified data
    """
    simplified_data = [simplify_message(msg) for msg in data.data]
    return json.dumps(simplified_data)


def get_math_response(question):
    """Get the response for the math question"""
    prompty_file = os.environ["PROMPTY_FILE"]
    path = f"./{prompty_file}"
    prompt_template = PromptTemplate.from_prompty(file_path=path)

    messages = prompt_template.create_messages(question=question)

    input = " ".join([json.dumps(entry) for entry in messages])

    with project_client:
        code_interpreter = CodeInterpreterTool()

        agent = project_client.agents.create_agent(
            model=os.environ["GPT4O_DEPLOYMENT_NAME"],
            name="math-agent",
            instructions=input,
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources,
        )

        thread = project_client.agents.create_thread()

        project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=question,
        )

        run = project_client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)

        while run.status in ["queued", "in_progress", "requires_action"]:
            # Wait for a second
            time.sleep(1)
            run = project_client.agents.get_run(thread_id=thread.id, run_id=run.id)

            print(f"Run status: {run.status}")

        if run.status == "failed":
            # Check if you got "Rate limit is exceeded.", then you want to get more quota
            print(f"Run failed: {run.last_error}")

        messages = project_client.agents.list_messages(thread_id=thread.id)
        print(f"Messages: {messages}")

        # Get the last message from the sender
        last_msg = messages.get_last_text_message_by_role("assistant")
        if last_msg:
            print(f"Last Message: {last_msg.text.value}")

        project_client.agents.delete_thread(thread.id)
        project_client.agents.delete_agent(agent.id)
        return {
            "response": last_msg.text.value, 
            "full_output": convert_and_serialize(messages)
        }


if __name__ == "__main__":
    # Test the math response
    load_dotenv()
    QUESTION = "Find (24^{-1} pmod{11^2})?"
    result = get_math_response(QUESTION)
    print(result)
