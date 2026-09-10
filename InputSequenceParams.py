from dataclasses import dataclass

@dataclass
class InputSequenceParams:
    output_path: str = "output.png"

    show_title: bool = False
    show_text: bool = True
    show_expanded: bool = False
    show_a_jump: bool = True
    show_b_jump: bool = True
    show_jump_button: bool = True

    colored_buttons: bool = True
    directional_colors: bool = True

    font_size: int = 32
    stroke_width: int = 2
    vertical_spacing: int = 1
    input_spacing: int = 0
    tech_spacing: int = 15
