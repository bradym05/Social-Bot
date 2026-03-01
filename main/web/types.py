from enum import StrEnum

# Name to button text
class VideoCrop(StrEnum):
    Original = "Original"
    Square = "1:1"
    Portrait = "9:16"
    Landscape = "16:9"