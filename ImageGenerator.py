from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path

icon_colors = {
    "A": ("#01a7a0", "right"),
    "AA": ("#F7122C", "right"),
    "AJ": ("#01a7a0", "right"),
    "B": ("#F7122C", "bottom"),
    "BA": ("#F7122C", "bottom"),
    "BJ": ("#01a7a0", "bottom"),
    "X": ("#F7122C", "top"),
    "Y": ("#F7122C", "left"),
    "ZL": "#3c59d7",
    "ZR": "#c408a2",
    "L": "#d7bb3c",
    "R": "#f08d2b",
}

def create_text_grid(
        rows,
        output_path,
        font_path,
        icons_path,
        separators,
        font_size=32,
        stroke_width=2,
        vertical_spacing=0,
        input_spacing=0,
        title="",
        title_spacing=8,
        title_font_size=None,
        gt_spacing=15,
        colored_buttons=True,
        directional_colors=True,
):

    font = ImageFont.truetype(font_path, font_size)
    nested_separator_font = ImageFont.truetype(
        font_path,
        int(font_size * 0.75)
    )

    if title_font_size is None:
        title_font_size = int(font_size * 1.2)
    title_font = ImageFont.truetype(font_path, title_font_size)

    icons_path = Path(icons_path)

    # Load and scale all icons.
    icons = {}

    for path in icons_path.glob("*.png"):
        icon = Image.open(path).convert("RGBA")

        side = None
        # Apply color if one is specified.
        try:
            color, side = icon_colors[path.stem]
        except KeyError:
            # No color for this button
            color = None
        except ValueError:
            # no side specified
            color = icon_colors[path.stem]
            side = None

        if color is not None and colored_buttons:
            icon = color_icon(
                icon,
                color,
                side if directional_colors else None
            )

        # Create stroke.
        if stroke_width != 0:
            alpha = icon.getchannel("A")

            stroke_size = stroke_width * 2 + 1

            expanded_alpha = alpha.filter(
                ImageFilter.MaxFilter(stroke_size)
            )

            stroke = Image.new(
                "RGBA",
                icon.size,
                (0, 0, 0, 255)
            )

            stroke.putalpha(expanded_alpha)

            stroke.alpha_composite(icon)

            icon = stroke

        # Scale icon.
        icon = icon.resize(
            (
                int(font_size * 1.2),
                int(font_size * 1.2)
            ),
            Image.Resampling.LANCZOS
        )

        icons[path.stem] = icon

    # Convert every cell to a list.
    normalized_rows = []

    for row in rows:
        normalized_row = []

        for cell in row:
            if isinstance(cell, list):
                normalized_row.append(cell)
            else:
                normalized_row.append([cell])

        normalized_rows.append(normalized_row)

    num_columns = 0
    if len(normalized_rows) != 0:
        num_columns = max(len(row) for row in normalized_rows)

    # Measure every cell.
    measurements = []

    for row in normalized_rows:
        row_measurements = []

        for cell in row:
            cell_width = 0
            cell_height = 0

            for index, element in enumerate(cell):
                if element in icons:
                    width, height = icons[element].size
                else:
                    is_nested_separator = len(cell) > 1 and element in separators and element not in ["(", ")", "[", "]", "{", "}"]
                    current_font = (
                        nested_separator_font
                        if is_nested_separator
                        else font
                    )

                    bbox = current_font.getbbox(
                        element,
                        stroke_width=stroke_width
                    )

                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    if not is_nested_separator and element == ">":
                        width += gt_spacing

                cell_width += width

                if index > 0:
                    cell_width += input_spacing

                cell_height = max(cell_height, height)

            row_measurements.append(
                (cell_width, cell_height)
            )

        measurements.append(row_measurements)

    # Find the widest cell in each column.
    column_widths = [0] * num_columns

    for row_measurements in measurements:
        for column, (width, height) in enumerate(row_measurements):
            column_widths[column] = max(
                column_widths[column],
                width
            )

    # Find the tallest row.
    row_heights = []

    for row_measurements in measurements:
        height = max(
            height
            for width, height in row_measurements
        )

        row_heights.append(height + vertical_spacing)

    # Calculate title dimensions.
    title_height = 0
    title_width = 0

    if title:
        title_bbox = title_font.getbbox(
            title,
            stroke_width=stroke_width
        )

        font_bbox = title_font.getbbox(
            "Pp",
            stroke_width=stroke_width
        )

        title_width = title_bbox[2] - title_bbox[0]
        title_height = font_bbox[3] - font_bbox[1]

        title_height += title_spacing

    image_width = max(sum(column_widths), title_width)
    image_height = sum(row_heights) + title_height

    image = Image.new(
        "RGBA",
        (image_width, image_height),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(image)

    # Draw title.
    if title:
        title_x = (
                          image_width - title_width
                  ) / 2 - title_bbox[0]

        title_y = -title_bbox[1]

        # Underline
        underline_y = (
                title_y
                + title_height/1.4
        )

        # Black stroke
        draw.line(
            (
                title_x-stroke_width,
                underline_y,
                title_x + title_width + stroke_width,
                underline_y
            ),
            fill=(0, 0, 0, 255),
            width=2 + stroke_width * 2
        )

        # White center
        draw.line(
            (
                title_x,
                underline_y,
                title_x + title_width,
                underline_y
            ),
            fill=(255, 255, 255, 255),
            width=2
        )

        draw.text(
            (title_x, title_y),
            title,
            font=title_font,
            fill=(255, 255, 255, 255),
            stroke_width=stroke_width,
            stroke_fill=(0, 0, 0, 255)
        )

    # Center the grid horizontally.
    grid_width = sum(column_widths)
    grid_x = (image_width - grid_width) / 2

    y = title_height

    for row_index, row in enumerate(normalized_rows):
        x = grid_x

        for column, cell in enumerate(row):
            cell_width = column_widths[column]
            cell_height = row_heights[row_index]

            # Calculate the actual width of this cell's contents.
            content_width = measurements[row_index][column][0]

            # Center the entire group of elements.
            element_x = (
                    x
                    + (cell_width - content_width) / 2
            )

            for element in cell:

                # Icon
                if element in icons:
                    icon = icons[element]

                    icon_x = int(element_x)
                    icon_y = int(
                        y + (cell_height - icon.height) / 2
                    )

                    image.alpha_composite(
                        icon,
                        (icon_x, icon_y)
                    )

                    element_x += icon.width

                # Text
                else:
                    is_nested_separator = (
                            len(cell) > 1
                            and element in separators
                            and element not in ["(", ")", "[", "]", "{", "}"]
                    )

                    current_font = (
                        nested_separator_font
                        if len(cell) > 1 and element in separators and element not in ["(", ")"]
                        else font
                    )

                    bbox = draw.textbbox(
                        (0, 0),
                        element,
                        font=current_font,
                        stroke_width=stroke_width
                    )

                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]

                    text_y = (y + (cell_height - text_height) / 2 - bbox[1])

                    extra_spacing = (
                        gt_spacing
                        if not is_nested_separator and element == ">"
                        else 0
                    )

                    # Half the extra space before the >
                    element_x += extra_spacing / 2

                    draw.text(
                        (element_x - bbox[0], text_y),
                        element,
                        font=current_font,
                        fill=(255, 255, 255, 255),
                        stroke_width=stroke_width,
                        stroke_fill=(0, 0, 0, 255)
                    )

                    element_x += text_width

                    # Half the extra space after the >
                    element_x += extra_spacing / 2

                # Space between elements in a cell.
                element_x += input_spacing

            x += cell_width

        y += row_heights[row_index]

    image.save(output_path, "PNG")

def color_icon(icon, color, side):
    width, height = icon.size

    # Original white icon
    result = icon.copy()

    # Mask for the colored half
    half_mask = Image.new("L", icon.size, 0)
    draw = ImageDraw.Draw(half_mask)

    if side is not None:
        if side.lower() == "left":
            draw.rectangle(
                (0, 0, width // 2, height),
                fill=255
            )

        elif side.lower() == "right":
            draw.rectangle(
                (width // 2, 0, width, height),
                fill=255
            )

        elif side.lower() == "top":
            draw.rectangle(
                (0, 0, width, height // 2),
                fill=255
            )

        elif side.lower() == "bottom":
            draw.rectangle(
                (0, height // 2, width, height),
                fill=255
            )
    else:
        draw.rectangle(
            (0, 0, width, height),
            fill=255
        )

    # Make sure we only color the actual icon,
    # not the transparent background.
    alpha = icon.getchannel("A")

    # Intersection of the geometric mask and icon alpha.
    half_mask = Image.composite(
        half_mask,
        Image.new("L", icon.size, 0),
        alpha
    )

    # Create colored version.
    colored = Image.new(
        "RGBA",
        icon.size,
        color
    )

    colored.putalpha(half_mask)

    # Put colored portion over original white icon.
    result.alpha_composite(colored)

    return result