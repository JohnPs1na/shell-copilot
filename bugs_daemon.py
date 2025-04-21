import time
import os
import re
import uuid
import requests
import fcntl

FILE_PATH = "/tmp/suggestions.txt"


def ensure_file_exists(file_path):
    if not os.path.exists(file_path):
        with open(file_path, "a"):
            pass

def tail_f(file_path):
    with open(file_path, "r") as f:
        fd = f.fileno()
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        
        while True:
            try:
                content = f.read()
                if content:
                    f.seek(0)
                    yield content
                    with open(file_path, "w") as clear_f:
                        clear_f.truncate(0)
                else:
                    time.sleep(0.1)
            except IOError:
                time.sleep(0.1)
                continue

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

        response = requests.post("http://localhost:8080/start_workflow", json=data).json()
        

        system_intent = response["intent_detection"]["intent"]

        if system_intent == "suggestion":
            suggestion = response["system_output"]["suggestion_prompt"]
            display_suggestion(terminal_id, suggestion)
        
        elif system_intent == "explanation":
            explanation = response["system_output"]["explanation_prompt"]
            display_suggestion(terminal_id, explanation)
        
        with open(FILE_PATH, "w") as f:
            f.truncate(0)
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