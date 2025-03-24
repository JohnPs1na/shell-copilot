from google import genai
import json
import os


class Chatbot:
    def __init__(self):
        with open("prompts.json") as f:
            prompts = json.load(f)
            self.suggestion_prompt = prompts["suggestion"]

        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


    def generate_suggestion(self, message):

        new_prompt = self.suggestion_prompt.replace("{message}",message)
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=new_prompt
        )

        return response.text

if __name__ == "__main__":
    pass
    # chatbot = Chatbot()
    #
    # print(chatbot.generate_suggestion("how do I enter a docker container"))
