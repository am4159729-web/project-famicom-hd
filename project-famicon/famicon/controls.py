from dataclasses import dataclass


@dataclass
class Controls:
    """One frame of input. Directions and a/b are held states; *_press fire on the frame of the key-down."""
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False
    a: bool = False
    b: bool = False
    up_press: bool = False
    down_press: bool = False
    left_press: bool = False
    right_press: bool = False
    a_press: bool = False
    b_press: bool = False
    start_press: bool = False
    back_press: bool = False
