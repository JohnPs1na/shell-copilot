import time
import os
import re
import uuid
import requests
import fcntl
import threading
import pika
import json

FILE_PATH = "/tmp/suggestions.txt"
ACTIVE_WORKFLOW_FILE = "/tmp/active_workflow.txt"
RABBITMQ_QUEUE = "ASSISTANT_QUEUE"


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

def display_message(terminal_id, message):

    tty_path = f"{terminal_id}"
    try:
        with open(tty_path, "w") as tty:
            tty.write("\033[90m" + message.strip() + "\033[0m")
            tty.flush()
    except Exception as e:
        print(f"Error writing to terminal {terminal_id}: {e}")

def process_line(line):
    try:

        terminal_id, user_message = line.strip().split("::::")
        
        random_uuid = uuid.uuid4()
        
        data = {
            "workflow_id": str(random_uuid),
            "message": user_message,
            "context": {
                "terminal_id": terminal_id,
                "timestamp": time.time()
            }
        }

        with open(ACTIVE_WORKFLOW_FILE, "w") as f:
            f.write(f"{random_uuid},{terminal_id}")

        response = requests.post("http://localhost:12345/start_workflow", json=data).json()
        
        system_intent = response["intent_detection"]["intent"]

        if system_intent == "suggestion":
            suggestion = response["system_output"]["suggestion_prompt"]
            display_message(terminal_id, suggestion)
        
        elif system_intent == "explanation":
            explanation = response["system_output"]["explanation_prompt"]
            display_message(terminal_id, explanation)
        

        with open(ACTIVE_WORKFLOW_FILE, "w") as f:
            f.truncate(0)
            f.flush()
            os.fsync(f.fileno())

        with open(FILE_PATH, "w") as f:
            f.truncate(0)
            f.flush()
            os.fsync(f.fileno())
            
    except Exception as e:
        print(f"Error processing line: {e}")

def rabbitmq_listener():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        print(f" [*] Waiting for messages in {RABBITMQ_QUEUE}. To exit press CTRL+C")
        
        def callback(ch, method, properties, body):
            try:
                message_data = json.loads(body)
                terminal_id = message_data.get("terminal_id", "")
                message = message_data.get("message", "")
                
                display_message(terminal_id, message)
                
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Error processing RabbitMQ message: {e}")
        
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)
        
        channel.start_consuming()
    except Exception as e:
        print(f"RabbitMQ connection error: {e}")
        time.sleep(5)
        rabbitmq_listener()


def file_monitor_thread():
    """Thread function to monitor the file and process lines"""
    ensure_file_exists(FILE_PATH)
    for line in tail_f(FILE_PATH):
        process_line(line)


def main():
    ensure_file_exists(ACTIVE_WORKFLOW_FILE)

    # Create and start the file monitor thread
    file_thread = threading.Thread(target=file_monitor_thread, daemon=True)
    file_thread.start()
    
    # Create and start the RabbitMQ listener thread
    rabbitmq_thread = threading.Thread(target=rabbitmq_listener, daemon=True)
    rabbitmq_thread.start()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    main()