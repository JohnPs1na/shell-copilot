#!/usr/bin/env python
import os
import sys
import requests
import fcntl

SUGGESTION_FILE_PATH = "/tmp/suggestions.txt"
ACTIVE_WORKFLOW_FILE = "/tmp/active_workflow.txt"

def ensure_file_exists(file_path):
    """
    Creates the file if it does not already exist.
    """
    if not os.path.exists(file_path):
        with open(file_path, "a"):
            pass

def write_with_lock(file_path, content):
    """
    Write to file with proper locking
    """
    with open(file_path, "w") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def main():
    ensure_file_exists(SUGGESTION_FILE_PATH)
    ensure_file_exists(ACTIVE_WORKFLOW_FILE)
    if not os.path.exists(SUGGESTION_FILE_PATH):
        print("Error: bugs server is not running.")
        return

    if len(sys.argv) < 1:
        print("Usage: bugs <message>")
        return

    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        active_workflow = ""

        with open(ACTIVE_WORKFLOW_FILE, "r") as f:
            content = f.readline()
            if content != "":
                active_workflow, terminal_name = content.split(",")
        
        if active_workflow == "":

            if sys.stdin.isatty():
                terminal_name = os.ttyname(sys.stdin.fileno())
            else:
                print("Not running in an interactive terminal.")

            write_with_lock(SUGGESTION_FILE_PATH, f"{terminal_name}::::{message}")
        
        else:
            try:
                data = {
                    "user_input": message
                }

                requests.post(f"http://localhost:12345/send_signal/{active_workflow}", json=data)

            except Exception as e:
                print("Error: Unable to send signal to workflow.")
                return


    else:
        print("There was an error")


if __name__ == "__main__":
    main()