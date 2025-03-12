import time
import os
import re

FILE_PATH = "/tmp/suggestions.txt"


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
            tty.write("\n")
            tty.flush()
    except Exception as e:
        print(f"Error writing to terminal {terminal_id}: {e}")

def process_line(line):

    print(line)
    with open(FILE_PATH,"r") as f:
        terminal_id, suggestion = f.readline().split(",")
        display_suggestion(terminal_id, suggestion)
    open(FILE_PATH,"w").close()


def main():

    for line in tail_f(FILE_PATH):
        process_line(line)

if __name__ == "__main__":
    main()