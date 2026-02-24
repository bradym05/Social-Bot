# Dependencies
from typing import List, Dict

import numpy as np
import time
import random


# Static Variables
special_upper = ['~','!','@','#','$','%','^','&','*','(',')','_','+','{','}','|',':','"','<','>','?']
special_lower = ["`","1","2","3","4","5","6","7","8","9","0","-","=","[","]","\\",";","'",",",".","/"]
special_translations = {special_upper[i]:v for i, v in enumerate(special_lower)}
keyboard_layout = [
    ["`","1","2","3","4","5","6","7","8","9","0","-","="],
    ["q","w","e","r","t","y","u","i","o","p","[","]","\\"],
    ["a","s","d","f","g","h","j","k","l",";","'"],
    ["z","x","c","v","b","n","m",",",".","/"]
    ]

# Declare typer class
class Typer:
    # Initialize object
    def __init__(
        self, 
        type_callback:callable, 
        speed:float=10, 
        typo_chance:float=0.05,
        typo_range:int=2
        ):
        # Initialize variables
        self.type_callback = type_callback
        self.speed = speed
        self.typo_chance = typo_chance
        self.typo_range = typo_range
        self.letter_cache = {}
    # Get keyboard position of a character
    def get_character_pos(self, char:str):
        # Initialize variables
        pos = np.full((2), -1, dtype=int)
        char = char.lower()
        # Check if character is special
        if char in special_translations:
            char = special_translations[char]
        # Check cache
        if char in self.letter_cache:
            pos = self.letter_cache[char]
        else:
            # Find x and y position iteratively
            for y, row in enumerate(keyboard_layout):
                # Check for character in row
                if row.count(char) > 0:
                    # Find x
                    for x, key in enumerate(row):
                        if key == char:
                            # Set x val
                            pos[0] = x
                            break
                    # Set y val
                    pos[1] = y
                    break
            # Cache result
            self.letter_cache[char] = pos
        return pos
    # Simulate typing, pass additional args
    def type_query(self, query:str="", *args):
        typed = ""
        final_char = len(list(query))
        next_char = 0
        typos = 0
        # Loop until completed
        while next_char < final_char:
            # Random chance of typo
            if query[next_char] != " " and next_char > 0 and random.random() < self.typo_chance and typos <= 2:
                # Get current keyboard position
                keyboard_position = self.get_character_pos(char=query[next_char])
                # Check if position is valid
                if np.all(keyboard_position >= 0):
                    # Randomly select a position within keyboard dimensions
                    x_offset, y_offset = random.randrange(-self.typo_range, self.typo_range, self.typo_range), random.randrange(-self.typo_range, self.typo_range, self.typo_range)
                    typo_y = min(max(keyboard_position[0] + y_offset, 0), len(keyboard_layout) - 1)
                    typo_x = min(max(keyboard_position[0] + x_offset, 0), len(keyboard_layout[typo_y]) - 1)
                    # Get character from position and indicate typo
                    typos += 1
                    char = keyboard_layout[typo_y][typo_x]
                else:
                    # Swap case by default
                    char = query[next_char].swapcase()
            elif typos > 0:
                # Undo previous typo
                typos -= 1
                char = ""
            else:
                # Type out next character
                char = query[next_char]
                next_char += 1
            # Check character ("" = backspace)
            if char == "":
                typed = typed[:-1]
            else:
                typed += char
            # Wait a short delay based on speed variable
            time.sleep(random.random()/self.speed)
            # Pass updated string to callback
            self.type_callback(typed, char, *args)