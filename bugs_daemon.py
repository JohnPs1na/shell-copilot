import time
import os
import re
import uuid
import requests

FILE_PATH = "/tmp/suggestions.txt"


def ensure_file_exists(file_path):
    if not os.path.exists(file_path):
        with open(file_path, "a"):
            pass

def tail_f(file_path):

    with open(file_path, "r") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

def display_suggestion(terminal_id, suggestion):

    tty_path = f"{terminal_id}"
    try:
        with open(tty_path, "w") as tty:
            tty.write("\033[90m" + suggestion.strip() + "\033[0m")
            tty.flush()
    except Exception as e:
        print(f"Error writing to terminal {terminal_id}: {e}")

def process_line(line):
    try:
        terminal_id, user_message = line.strip().split(",")
        
        random_uuid = uuid.uuid4()
        
        data = {
            "workflow_id": str(random_uuid),
            "message": user_message,
            "context": {
                "terminal_id": terminal_id,
                "timestamp": time.time()
            }
        }

        response = requests.post("http://localhost:8080/start_workflow", json=data)
        suggestion = response.json()["system_output"]["suggestion_prompt"]
        
        display_suggestion(terminal_id, suggestion)
        
        with open(FILE_PATH, "w") as f:
            f.write("")
            f.flush()
            os.fsync(f.fileno())
            
    except Exception as e:
        print(f"Error processing line: {e}")


def main():

    ensure_file_exists(FILE_PATH)
    for line in tail_f(FILE_PATH):
        process_line(line)

if __name__ == "__main__":
    main()