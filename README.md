## Social Bot

Automatically scroll through instagram, like posts, and follow people using AI. The bot's "personality" is determined by the following inputs:
- Interests
- Goals
- Grammar Instructions
- Sample Responses
- Slang

For more information, see this [Example](Example.py)

## Demo Video

[![Demo Video Thumbnail](https://img.youtube.com/vi/efR3fxPRBXo/0.jpg)](https://www.youtube.com/watch?v=efR3fxPRBXo)

## Requirements Installation

To get started with this project, you need to install the required packages. Follow the steps below:

1. **Create a virtual environment (optional but recommended)**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\ScriptsActivate`
    ```

2. **Install the required packages**:
    ```bash
    pip install -r requirements.txt
    ```

## Model Setup

You will need to download 2 models in gguf file format.

1. **Text Generation**:

    Download [Lexi Llama 3 Uncensored](https://huggingface.co/bartowski/Lexi-Llama-3-8B-Uncensored-GGUF) and add the path to [config.ini](config.ini)
    ```ini
    LLAMA_PATH = PATH TO MODEL
    ```

2. **Image to Text**:

    Download [Nano Llava](https://huggingface.co/abetlen/nanollava-gguf) and add both paths to [config.ini](config.ini)
    Make sure you download both the clip (mmproj) and image-text files
    ```ini
    NANOLLAVA_PATH = PATH TO MODEL
    NANOLLAVA_CLIP_PATH = PATH TO CLIP MODEL (mmproj)
    ```