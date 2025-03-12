#!/usr/bin/env python
import os
import sys
import httpx
import asyncio


SUGGESTION_FILE_PATH = "/tmp/suggestions.txt"

def ensure_file_exists(file_path):
    """
    Creates the file if it does not already exist.
    """
    if not os.path.exists(file_path):
        with open(file_path, "a"):
            pass


def main():
    ensure_file_exists(SUGGESTION_FILE_PATH)
    # Ensure the named pipe exists
    if not os.path.exists(SUGGESTION_FILE_PATH):
        print("Error: bugs server is not running.")
        return

    if len(sys.argv) < 2:
        print("Usage: bugs <command> <message>")
        return


    command = sys.argv[1]

    keywords = ["suggest", "say"]
    #Classifier intent maybe

    if command in keywords and len(sys.argv) > 2:
        message = " ".join(sys.argv[2:])
        # Send command to the server via the pipe
        print(message)

        terminal_name = "/dev/pts/4"

        if sys.stdin.isatty():
            terminal_name = os.ttyname(sys.stdin.fileno())
            print("Active terminal:", terminal_name)
        else:
            print("Not running in an interactive terminal.")

        with open(SUGGESTION_FILE_PATH, "w") as file:
            file.write(terminal_name+","+message)
    else:
        print("There was an error")


if __name__ == "__main__":
    main()