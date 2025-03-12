import time
import os
import re

# File that holds suggestions with terminal ids.
FILE_PATH = "/tmp/suggestions.txt"


def tail_f(file_path):
    """
    Generator that yields new lines appended to the file.
    Similar to tail -f.
    """
    with open(file_path, "r") as f:
        # Go to the end of file
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

def display_suggestion(terminal_id, suggestion):
    """
    Writes the suggestion text to the terminal with the given terminal id.
    The text is printed in gray using ANSI escape sequences.
    """
    tty_path = f"{terminal_id}"
    try:
        # Open the terminal device file in write mode.
        with open(tty_path, "w") as tty:
            # ANSI escape for gray is "\033[90m", and "\033[0m" resets the formatting.
            tty.write("\033[90m" + suggestion.strip() + "\033[0m")
            # Optionally, add a newline so the suggestion is on its own line.
            tty.write("\n")
            tty.flush()
    except Exception as e:
        # You might want to log errors appropriately in production.
        print(f"Error writing to terminal {terminal_id}: {e}")

def process_line(line):
    """
    Parses a line in the format 'terminal_id: suggestion text' and displays it.
    """
    print(line)
    with open(FILE_PATH,"r") as f:
        terminal_id, suggestion = f.readline().split(",")
        display_suggestion(terminal_id, suggestion)
    open(FILE_PATH,"w").close()


def main():

    # This loop runs indefinitely, reading new lines as they are appended to the file.
    for line in tail_f(FILE_PATH):
        process_line(line)

if __name__ == "__main__":
    main()