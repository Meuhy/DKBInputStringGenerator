import argparse
import os
import sys
import re

from ImageGenerator import create_text_grid
from InputSequenceParams import InputSequenceParams

# Bridge skip: Aim>Release>LCTJ>Unsurf>AFAT>FART>Unsurf>CDJ>Catch relefat>Stall fart>Unsurf>Chunk jump

# SA, SB, SX, SY inputs are inputs that will get translated when going from A jump to B jump.
# "SA" will show up as A on A jump and B on B jump.
move_inputs_a_jump = {"Jump": "SA", "Surf Jump": "SA", "Surf": "ZL", "Unsurf": "ZL", "Boost": "SX", "Attack": "SX", "Swing": "Y",
                      "Down Swing": "SB", "Up Swing": "X", "Neutral Swing": "Y", "Stall": "Y", "Punch": "Y",
                      "Forward Punch": "Y", "Up Punch": "X", "Down Punch": "SB", "DivePunch": "SB", "Chunk Jump": "SA",
                      "Drop": "R", "Clap": "R", "Sing": "L", "Throw": "ZR", "Grab": "ZR", "Chunk Catch": "ZR",
                      "Pull Ball": "ZR", "Aim": "Hold$ZR", "Cancel Aim": "R", "Release": "Release$ZR", "Roll": "ZL",
                      "Kong": "Kong", "Ostrich": "Ostrich", "Zebra": "Zebra", "Elephant": "Elephant", "Snake": "Snake",
                      "Drumbeat": "L+R", "Transform": "L+R", "Detransform": "L+R", "WallJump": "SA",
                      "WallDrop": "SB", "Right": "Right", "Left": "Left", "Forward": "Up", "Back": "Down",
                      "Neutral": "Neutral", "Neutral Drop": "Neutral$SB", "Test": "White$White",
                      "Pause": "Plus", "Map": "Minus", "Skills Menu": "Dpad Up", "Photo Mode": "Dpad Down",
                      "Center Camera": "R Click", "Twirl": "SA+SX", "Speedup": "SX", "Cutscene skip": "Plus/Minus"
                      }
techs = {"Rollpunch": "Roll > Punch",
         "Rolljump": "Roll > Jump",
         "AFAT": "Jump > Surf > (Attack+jump)",
         "Surf AFAT": "Surf Jump > Unsurf > Surf > (Attack+jump)",
         "FAT": "Jump (hold) > Surf > Attack",
         "FART": "Throw > (Roll > Grab) > (Surf > Attack+Jump)",
         "CTJ": "Grab > Wait 8f",
         "LCTJ": "Grab > Surf>Boost",
         "CDJ": "Down swing > Drop",
         "CRJ": "(Chunk jump > Chunk Catch) > (Surf > Attack+Jump)",
         "Stall CRJ": "Stall > (Chunk jump > Chunk Catch) > (Surf > Attack+Jump)",
         "Elefat": "(Chunk Jump > Pull Ball) > (Surf > Attack+Jump)",
         "Elefart": "(Roll > Pull Ball) > (Surf > Attack+Jump)",
         "Relefat": "Roll > (Jump > Pull Ball) > (Surf > Attack+Jump)",
         "Fartephant": "Throw > Roll > Grab > (Surf > Attack+Jump)",
         "Stall Fartephant": "(Down Swing > Throw) > Roll > Grab > (Surf > attack+Jump)",
         "Catch Elefat": "(Chunk jump>Chunk Catch) > (Surf > Attack+Jump)",
         "Catch Relefat": "Roll > Jump>Chunk Catch > (Surf > Attack+Jump)",
         "Stall FART": "Down Swing > Throw > (Roll > Grab) > (Surf > Attack+Jump)",
         "WallDrop AFAT": "Neutral Drop > Left(Surf > Attack+Jump)",
         "Normalize Cam": "Aim > Cancel Aim",
         "Juice Boost": "Transform > Grab > Surf > Mash $Jump",
         "IFAT": "Repeat (Unsurf > Surf > Attack+Jump)",
         "Flutter Stall": "Repeat (Surf+Stall)",
         "Junction Bridge Skip": "Aim > Release > LCTJ > Unsurf > AFAT > FART > Unsurf > CDJ > Catch Relefat > Unsurf > Stall fart > Unsurf > Chunk jump"
         }
separators = {">", "(", ")", "+", "/", "$", "[", "]", "{", "}"}

def remove_separator_spaces(text):
    separator_pattern = "|".join(re.escape(s) for s in separators)

    return re.sub(
        rf"\s*({separator_pattern})\s*",
        r"\1",
        text
    )


def flatten_recursive(row):
    out = []
    for token in row:
        if isinstance(token, list):
            out.extend(flatten_recursive(token))
        else:
            out.append(token)
    return out


def flatten_to_two_levels(items):
    return [
        flatten_recursive(item) if isinstance(item, list) else item
        for item in items
    ]


def clean_word(word):
    if isinstance(word, list):
        clean_list = []
        for sub_word in word:
            clean_list.append(clean_word(sub_word))
        return clean_list
    else:
        return word[0].upper() + word[1:].lower()

def expand_tokens(tokens):
    expanded = []
    for token in tokens:
        if token in techs.keys():
            expanded_token = expand_tokens(parse_input(techs[token]))
            expanded.append(expanded_token)
        else:
            expanded.append(token)
    return expanded


def group_additive_tokens(tokens):
    i = 0

    while i < len(tokens):
        if (
                token := tokens[i]
        ) == "+" and (
                0 < i < len(tokens) - 1
                and not isinstance(tokens[i - 1], list)
                and not isinstance(tokens[i + 1], list)
        ):
            tokens[i - 1:i + 2] = [[
                tokens[i - 1],
                tokens[i],
                tokens[i + 1]
            ]]

            # Move past the newly created group.
            i -= 1

        i += 1

    return tokens


def parse_input(text):
    moves = move_inputs_a_jump.keys()
    tokens = []

    text = remove_separator_spaces(text)

    i = 0

    while i < len(text):
        # Is this character a separator?
        if text[i] in separators:
            if text[i] != "$":
                tokens.append(text[i])
            i += 1
            continue

        # Otherwise, read until the next separator
        start = i

        while i < len(text) and text[i] not in separators:
            i += 1

        word = text[start:i]

        # Capitalize the first letter
        word_clean = clean_word(word)
        clean_moves = {
            clean_word(move): move
            for move in moves
        }
        clean_techs = {clean_word(k): k for k in techs.keys()}

        # Tech replacement
        if word_clean in clean_techs.keys():
            tech_text = clean_techs[word_clean]
            tokens.append(tech_text)

        elif word_clean in clean_moves:
            tokens.append(clean_moves[word_clean])
        else:
            tokens.append(word)

    return tokens


# Keycodes: SA, SB, SX, SY = buttons with A jump
def b_jumpers_moment(keycode, b_jump):
    if isinstance(keycode, list):
        return [b_jumpers_moment(single_keycode, b_jump) for single_keycode in keycode]
    else:
        if not b_jump:
            if keycode.upper() == "SA":
                return "AJ" # A as a jump
            elif keycode.upper() == "SB":
                return "BA" # B as an attack
            elif keycode.upper() == "SX":
                return "X"
            elif keycode.upper() == "SY":
                return "Y"
            else:
                return keycode
        else:
            if keycode.upper() == "SA":
                return "BJ" # B as a jump
            elif keycode.upper() == "SB":
                return "AA" # A as an attack
            elif keycode.upper() == "SX":
                return "Y"
            elif keycode.upper() == "SY":
                return "X"
            else:
                return keycode


def create_inputs_string(seq, move_inputs, b_jump=False):
    inputs = []
    clean_move_inputs = {clean_word(k): v for k, v in move_inputs.items()}
    for token in seq:
        if isinstance(token, list):
            parsed = create_inputs_string(token, move_inputs, b_jump)
            inputs.append(parsed)
        elif clean_word(token) in clean_move_inputs.keys():
            parsed_inputs = parse_input(move_inputs[token])
            if len(parsed_inputs) == 1:
                parsed_inputs = parsed_inputs[0]

            parsed_inputs = b_jumpers_moment(parsed_inputs, b_jump)
            inputs.append(parsed_inputs)
        else:
            inputs.append(token)
    return inputs


def resource_path(relative_path):
    """Get the path to a bundled resource."""
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


def generate_input_sequence(seq_string, params, title=""):
    if not params.show_title:
        title = ""

    move_seq = parse_input(seq_string)
    expanded_seq = expand_tokens(move_seq)
    if params.show_expanded and not params.show_text:
        expanded_seq = flatten_recursive(expanded_seq)
    expanded_seq = flatten_to_two_levels(group_additive_tokens(expanded_seq))

    input_seq_a_jump = flatten_to_two_levels(create_inputs_string(expanded_seq, move_inputs_a_jump))
    input_seq_b_jump = flatten_to_two_levels(create_inputs_string(expanded_seq, move_inputs_a_jump, True))

    if params.show_jump_button and (params.show_a_jump or params.show_b_jump):
        move_seq.insert(0, "")
        expanded_seq.insert(0, "")
        input_seq_a_jump.insert(0, "A Jump: ")
        input_seq_b_jump.insert(0, "B Jump: ")
        # input_seq_a_jump.insert(0, ["AJ", "Jump: "])
        # input_seq_b_jump.insert(0, ["BJ", "Jump: "])

    font_path = resource_path("fonts/adlib.ttf")
    icons_path = resource_path("icons")

    rows = []
    if params.show_text:
        rows.append(move_seq)
    if params.show_expanded:
        rows.append(expanded_seq)
    if params.show_a_jump:
        rows.append(input_seq_a_jump)
    if params.show_b_jump:
        rows.append(input_seq_b_jump)

    print(rows)

    create_text_grid(
        rows,
        params.output_path,
        font_path,
        icons_path,
        separators,
        font_size=params.font_size,
        stroke_width=params.stroke_width,
        vertical_spacing=params.vertical_spacing,
        input_spacing=params.input_spacing,
        title=title,
        gt_spacing=params.tech_spacing,
        colored_buttons=params.colored_buttons,
        directional_colors=params.directional_colors
    )


if __name__ == '__main__':
    # for move in move_inputs_a_jump.keys():
    #     print(move, end=", ")

    # for tech, input_seq in techs.items():
    #     print(f"{tech}: {input_seq}")

    parser = argparse.ArgumentParser(
        description="Generate an input sequence PNG."
    )

    parser.add_argument(
        "-is",
        "--input_string",
        help="Input sequence, e.g. 'jump>surf>(attack+jump)'",
        default=""
    )

    parser.add_argument(
        "-f",
        "--font-size",
        type=int,
        default=32,
        help="Font size (default: 32)"
    )

    parser.add_argument(
        "-o",
        "--output",
        default="output.png",
        help="Output PNG filename (default: output.png)"
    )

    args = parser.parse_args()

    input_string = args.input_string

    infinite_mode = False
    if input_string == "":
        infinite_mode = True

    start_over = True
    while start_over:
        if infinite_mode:
            input_string = input("Enter the move sequence to be converted to PNG, or 'exit'\n")

        if input_string.upper() == "EXIT" or input_string.upper() == "STOP":
            start_over = False
            break

        seq_params = InputSequenceParams()
        seq_params.title = "Ostrichless Junction Bridge Skip Inputs"
        seq_params.font_size = args.font_size
        seq_params.output_path = args.output

        generate_input_sequence(input_string, seq_params)

        start_over = infinite_mode
