# Dependencies
from langchain_core.prompts import PromptTemplate
from llama_cpp import Llama
from llama_cpp.llama_chat_format import NanoLlavaChatHandler
from typing import Optional, List

import re
import atexit
import configparser

# Load config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# SETTINGS
LLAMA_PATH = config["models"]["LLAMA_PATH"]
NANOLLAVA_PATH = config["models"]["NANOLLAVA_PATH"]
NANOLLAVA_CLIP_PATH = config["models"]["NANOLLAVA_CLIP_PATH"]
DEFAULT_CHAT_INSTRUCTIONS = """
You are NOT an AI assistant. You are a real person leaving comments on social media.
Your writing is casual, messy, and human.
- Use slang, abbreviations, and emojis when it fits.
- Do NOT be polite or formal. No corporate tone, no essay-style sentences.
- It’s fine to use run-on sentences, fragments, and imperfect grammar.
- You NEVER explain yourself, you just drop a short comment like any other user.
"""
DEFAULT_IMG_INSTRUCTIONS = f"You perfectly describe key details of images. {DEFAULT_CHAT_INSTRUCTIONS}"
CONTEXT_LENGTH = 2048

# Base LLM class
class BaseLLM():
    # Initialize object
    def __init__(
        self, 
        chat_context:str="",
        chat_instructions:str="", 
        img_instructions:str="", 
        max_tokens:int=128, 
        cuda:bool=True,
        filtered_words:List[str]=[]
        ):
        # Setup main chat model
        self.llm = Llama(
            model_path=rf"{LLAMA_PATH}", 
            n_gpu_layers=-1 if cuda else 0, 
            n_batch=512, 
            n_ctx=CONTEXT_LENGTH * 2, 
            chat_format="llama-3")
        # Setup image chat model
        self.chat_context = chat_context
        self.nanollava_handler = NanoLlavaChatHandler(clip_model_path=rf"{NANOLLAVA_CLIP_PATH}") # Image clip model
        self.nanollava = Llama(
            model_path=rf"{NANOLLAVA_PATH}", 
            chat_handler=self.nanollava_handler, 
            n_gpu_layers=5 if cuda else 0, 
            n_batch=128, 
            n_ctx=CONTEXT_LENGTH, 
            n_threads=8
            )
        # Initialize variables
        self.filtered_words = filtered_words
        self.chat_instructions = chat_instructions if len(chat_instructions) > 0 else DEFAULT_CHAT_INSTRUCTIONS
        self.img_instructions = img_instructions if len(img_instructions) > 0 else DEFAULT_IMG_INSTRUCTIONS
        self.max_tokens = max_tokens
        # Close models on program exit
        atexit.register(self.llm.close)
        atexit.register(self.nanollava.close)
    # Process image using NanoLLava
    def describe_image(self, image_url:str, message:Optional[str]="", **kwargs) -> str:
        try:
            # Reset first
            self.nanollava.reset()
            # Get model output
            output = self.nanollava.create_chat_completion(
                messages = [
                    {"role": "system", "content": self.img_instructions},
                    {
                        "role": "user",
                        "content": [
                            {"type" : "text", "text": message},
                            {"type": "image_url", "image_url": {"url":image_url}}
                            ]
                    }
                ],
                max_tokens=self.max_tokens,
                stop=["###", "<|endoftext|>"],
                **kwargs
            )
            # Retrieve and return output message
            return output['choices'][0]['message']['content']
        except ValueError:
            print("MAX TOKENS EXCEEDED")
            return ""
    # Get processed response from Ollama
    def get_response(self, messages:str|List[str], instructions:str|None=None, **kwargs) -> str:
        # Reconcile messages to list
        if type(messages) == str:
            messages = [messages]
        # Check for custom instructions
        if instructions == None:
            instructions = self.chat_context + "\n" + self.chat_instructions
        # Create input
        input_messages = [{"role": "system", "content": instructions}]
        for m in messages:
            if len(m) > 0:
                input_messages.append({
                    "role": "user",
                    "content": m
                })
        try:
            # Reset first
            self.llm.reset()
            # Get model output
            output = self.llm.create_chat_completion(
                messages = input_messages,
                max_tokens=self.max_tokens,
                **kwargs
            )
            # Retrieve output message
            output_message = output['choices'][0]['message']['content']
            # Remove any filtered words
            for word in self.filtered_words:
                output_message = re.sub(word, "", output_message, flags=re.IGNORECASE)
            return output_message
        except ValueError:
            print("MAX TOKENS EXCEEDED")
            return ""