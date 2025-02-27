import uuid

import requests

base_url = "http://0.0.0.0:8123"


def create_assistant(assistant_id, assistant_name, graph_name):
    url = f"{base_url}/assistants"
    payload = {
        "assistant_id": assistant_id,
        "graph_id": graph_name,
        "config": {},
        "metadata": {},
        "if_exists": "raise",
        "name": assistant_name,
    }
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, json=payload, headers=headers)
    print("Assistant created", response.text, "\n")


def get_graph(assistant_id):
    url = f"{base_url}/assistants/{assistant_id}/graph"
    headers = {"Content-Type": "application/json"}
    response = requests.request("GET", url, headers=headers)
    print("Graph", response.text)


def create_thread(thread_id):
    url = f"{base_url}/threads"
    payload = {"thread_id": thread_id, "metadata": {}, "if_exists": "raise"}
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, json=payload, headers=headers)
    print("Thread created", response.text, "\n")


def run(assistant_id, thread_id, text):
    import requests

    url = f"{base_url}/threads/{thread_id}/runs/wait"

    payload = {
        "assistant_id": assistant_id,
        "input": {"messages": [{"role": "user", "content": text}]},
        "metadata": {},
        "if_not_exists": "reject",
        "after_seconds": 1,
    }
    headers = {"Content-Type": "application/json"}

    response = requests.request("POST", url, json=payload, headers=headers)
    return response


def main():
    first_run = False # Set to True to create a new assistant
    assistant_id = "1b8bb229-15eb-4d64-a52e-38ca1ac54da4"
    thread_id = "362bae49-3bf9-4ee6-bae4-830c54f52e85"
    message = "Hello"

    if first_run:
        assistant_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())
        assistant_name = f"assistant-{assistant_id}"
        graph_name = "agent"
        create_assistant(assistant_id, assistant_name, graph_name)
        create_thread(thread_id)

    result = run(assistant_id, thread_id, message)
    messages = result.json()["messages"]
    for message in messages:
        print(f"{message['type']}: {message['content']}")


if __name__ == "__main__":
    main()
