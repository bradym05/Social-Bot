## Social Bot

Automatically scroll through instagram, like posts, and follow people using AI. The bot's "personality" is determined by the following inputs:
- Interests
- Goals
- Grammar Instructions
- Sample Responses
- Slang
- Role
- Platform Usage

First, a query is generated to search for instagram posts based on a list of interests. A post is chosen at random, and its thumbnail is sent to the image-text model to generate a short description of the image. This description along with the comments, image alt text, and post caption are used to generate a search query to fill in any gaps (current events, up to date information, etc). This information is combined into one prompt for the text model which will return two values:
- INTEREST %: The LLM determines to what extent the given post aligns with its personality
- COMMENT: The LLM makes informed comments by reviewing other user's comments, and searching the internet for relevant information

Features:
- Login to account
- Generate queries and search on feed
- Scroll through feed
- Like posts that match interests
- Comment on posts that match interests
- Follow the followers of users who make posts that match interests
- Crop and upload videos
- Research post topics on DuckDuckGo before commenting

For more information, see this [Example](Example.py)

## Demo Video

[![Demo Video Thumbnail](https://img.youtube.com/vi/efR3fxPRBXo/0.jpg)](https://www.youtube.com/watch?v=efR3fxPRBXo)

## Installation

Requirements:

    - Python 3.12
    - C compiler
        - Linux: gcc or clang
        - Windows: Visual Studio or MinGW
        - MacOS: Xcode

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
