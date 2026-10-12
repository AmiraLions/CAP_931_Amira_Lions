# API CONNECTION TEST
# This script checks whether our API key works and whether we can
# request a response from GPT-4.1 mini.
# Running it sends one small paid request to OpenAI.

# Import the function that loads settings from our local .env file.
from dotenv import load_dotenv

# Import the client used to communicate with the OpenAI API.
from openai import OpenAI

# Read .env from the current working folder.
# Make its settings available to this Python process.
# This does not print the API key.
load_dotenv(".env")

# Create an API client.
# It automatically reads the OPENAI_API_KEY environment setting.
client = OpenAI()

# Send a short request and store the result in response.
# model selects the model used by this script, independently
# of the model selected in our ChatGPT conversation.
# input contains the instruction we send.
# max_output_tokens limits the length of the generated reply.
response = client.responses.create(
    model="gpt-4.1-mini",
    input="Reply with exactly: API connection successful",
    max_output_tokens=30,
)

# Display the model's reply.
print(response.output_text)

# Display the model identifier reported by OpenAI.
# It may include a version date.
print("Model:", response.model)

# Display token usage so we can understand and track API costs.
# Input tokens represent text sent; output tokens represent text generated.
print("Usage:", response.usage)