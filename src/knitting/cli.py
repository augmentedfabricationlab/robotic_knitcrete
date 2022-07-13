import json
import math
import os
import random
import typing as t
from datetime import datetime

import click
import numpy as np
import pandas as pd
from PIL import Image

DATE_FORMAT = "%Y%m%d-%H%M%S"


class UnimplementedInputFileFormat(Exception):
    """Raised when the input file format is not implemented"""

    pass


class InvalidPattern(Exception):
    """Raised when the input pattern is invalid"""

    pass


class UnknownKnitOperation(Exception):
    """Raised when the input pattern contains an unknown operation"""

    def __init__(self, op: str):
        self.op = op

    pass


class EmptyCellFound(Exception):
    """Raised when the input pattern contains an empty cell (nan)"""

    pass


class UnknownColor(Exception):
    """Raised when a pattern contains a color not mapped to any operations"""

    def __init__(self, color: t.List[float]):
        self.color = color

    pass


def get_dictionary_from_file(filepath: str) -> t.Dict[str, t.Any]:
    with open(filepath, "r") as file:
        return json.load(file)


def extract_pattern_data(filepath: str) -> t.Tuple[t.List[np.ndarray], t.List[str]]:
    extraction_map = {
        ".txt": extract_pattern_data_from_text,
        ".xlsx": extract_pattern_data_from_excel,
    }
    extension = get_extension_from_path(filepath)
    try:
        return extraction_map[extension](filepath)
    except KeyError:
        raise UnimplementedInputFileFormat


def get_filename_from_path(filepath: str) -> str:
    return os.path.splitext(os.path.basename(filepath))[0]


def get_extension_from_path(filepath: str) -> str:
    return os.path.splitext(os.path.basename(filepath))[1]


def extract_pattern_data_from_text(
    filepath: str,
) -> t.Tuple[t.List[np.ndarray], t.List[str]]:
    try:
        str_ops_matrices = [np.loadtxt(filepath, dtype=str)]
    except ValueError:
        raise InvalidPattern
    names = [get_filename_from_path(filepath)]
    return str_ops_matrices, names


def extract_pattern_data_from_excel(
    filepath: str,
) -> t.Tuple[t.List[np.ndarray], t.List[str]]:
    sheet_names = pd.ExcelFile(filepath).sheet_names
    df = pd.read_excel(filepath, sheet_name=sheet_names, header=None)
    str_ops_matrices = [np.array(sheet) for sheet in df.values()]
    filename = get_filename_from_path(filepath)
    names = [f"{filename}-{sheet}" for sheet in sheet_names]
    return str_ops_matrices, names


def get_2d_matrix_size_x(matrix: np.ndarray) -> int:
    return len(matrix[0])


def get_2d_matrix_size_y(matrix: np.ndarray) -> int:
    return len(matrix)


def get_output_path(basefolder: str, subfolder: str, filename: str) -> str:
    directory = os.path.join(basefolder, subfolder)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return os.path.join(directory, filename)


def tessellate_with_unit(
    unit: np.ndarray,
    image_width: int,
    image_height: int,
) -> np.ndarray:
    multiplier_x = image_width // get_2d_matrix_size_x(unit)
    multiplier_y = image_height // get_2d_matrix_size_y(unit)
    return np.tile(unit, (multiplier_y, multiplier_x))[:image_height, :image_width]


def generate_image(
    operations_map: t.Dict[str, t.List[float]], ops_matrix: np.ndarray
) -> Image.Image:
    try:
        rgb_ops_matrix = tuple(
            tuple(operations_map[key] for key in arr) for arr in ops_matrix
        )
    except KeyError as exc:
        if str(exc) == "nan":
            raise EmptyCellFound
        else:
            raise UnknownKnitOperation(op=str(exc))
    return Image.fromarray(np.array(rgb_ops_matrix).astype("uint8"))


def extract_rgb_matrix(filepath: str) -> np.ndarray:
    img = Image.open(filepath)
    return np.asarray(img)


def get_operation_from_rgb(
    operations_map: t.Dict[str, t.List[float]], color: t.List[float]
) -> str:
    try:
        return get_key_from_dictionary_list_value(operations_map, color)
    except IndexError:
        raise UnknownColor(color)


def get_key_from_dictionary_list_value(
    base_dict: t.Dict[str, t.Any], list_value: t.List[t.Any]
) -> str:
    return [name for name, op in base_dict.items() if np.array_equal(list_value, op)][0]


def strnow() -> str:
    return str(datetime.now().strftime(DATE_FORMAT))


def process_ops_matrix_per_row(
    density_start: float,
    density_end: float,
    str_ops_matrix: t.List[t.List[str]],
    source_key: str,
    target_key: str,
) -> t.Generator[t.List[str], None, None]:
    density_factors_per_row = np.linspace(
        density_start, density_end, get_2d_matrix_size_y(str_ops_matrix)
    )
    return (
        process_row(source_key, target_key, ops_row, d_factor)
        for ops_row, d_factor in zip(str_ops_matrix, density_factors_per_row)
    )


def process_row(
    source_key: str, target_key: str, ops_row: t.List[str], d_factor: np.float64
) -> t.List[str]:
    candidates = [idx for idx, item in enumerate(ops_row) if item == source_key]
    replacement_amount = math.floor((1 - d_factor) * len(candidates))
    replacement_indices = random.sample(candidates, replacement_amount)
    return [
        target_key if i in replacement_indices else original
        for i, original in enumerate(ops_row)
    ]


def process_ops_matrix_with_attractor(
    str_ops_matrix: t.List[t.List[str]],
    transfer_percentage: int,
    attractor_uv: t.Tuple[float, float],
    source_key: str,
    target_key: str,
) -> np.ndarray:
    image_width = get_2d_matrix_size_x(str_ops_matrix)
    image_height = get_2d_matrix_size_y(str_ops_matrix)
    processed_str_ops_matrix = process_attractor(
        transfer_percentage,
        attractor_uv,
        source_key,
        target_key,
        image_width,
        image_height,
        str_ops_matrix,
    )
    return processed_str_ops_matrix


def process_attractor(
    transfer_percentage: int,
    attractor_uv: t.Tuple[float, float],
    source_key: str,
    target_key: str,
    image_width: int,
    image_height: int,
    str_ops_matrix: t.Generator[t.List[str], None, None],
) -> np.ndarray:
    flattened_operations_matrix = [
        item for sublist in str_ops_matrix for item in sublist
    ]
    attractor_pos = get_attractor_position(attractor_uv, image_width, image_height)
    front_back_indices = [
        idx
        for idx, value in enumerate(flattened_operations_matrix)
        if value == source_key
    ]
    weighted_distances_from_attractor = [
        get_weighted_distance(image_width, attractor_pos, idx, 0.2)
        for idx in front_back_indices
    ]
    np.random.seed()
    transfer_indices = np.random.choice(
        front_back_indices,
        int(len(front_back_indices) * transfer_percentage / 100),
        p=get_field_probabilities(weighted_distances_from_attractor),
    )
    for idx in transfer_indices:
        flattened_operations_matrix[idx] = target_key
    return np.reshape(flattened_operations_matrix, (image_height, image_width))


def get_field_probabilities(
    weighted_distances_from_attractor: t.List[float],
) -> t.List[float]:
    max_distance = max(weighted_distances_from_attractor)
    distances = [
        max_distance - distance for distance in weighted_distances_from_attractor
    ]
    return [distance / sum(distances) for distance in distances]


def get_weighted_distance(
    image_width: int,
    attractor_pos: t.Tuple[int, int],
    idx: int,
    pull_factor: float,
) -> float:
    attractor_column, attractor_row = attractor_pos
    column = get_column_from_index(image_width, idx)
    row = get_row_from_index(image_width, idx)
    euclidean_dist = math.hypot(attractor_column - column, attractor_row - row)
    return euclidean_dist**pull_factor


def get_attractor_position(
    attractor_uv: t.Tuple[float, float], image_width: int, image_height: int
) -> t.Tuple[int, int]:
    column = int((image_width - 1) * attractor_uv[0])
    row = int((image_height - 1) * attractor_uv[1])
    return (column, row)


def get_row_from_index(matrix_width: int, idx: int) -> int:
    return idx // matrix_width


def get_column_from_index(matrix_width: int, idx: int) -> int:
    return idx % matrix_width


def get_hsv_matrix(rgb_matrix: str) -> t.List[t.List[t.Tuple[float, float, float]]]:
    return [[rgb_to_hsv(*value) for value in row] for row in rgb_matrix]


def rgb_to_hsv(red: float, green: float, blue: float) -> t.Tuple[float, float, float]:
    # Adapted from:
    # https://www.w3resource.com/python-exercises/math/python-math-exercise-77.php
    red = red / 255.0
    green = green / 255.0
    blue = blue / 255.0
    maximum = max(red, green, blue)
    minimum = min(red, green, blue)
    range = maximum - minimum

    if maximum == minimum:
        hue = 0
    elif maximum == red:
        hue = (60 * ((green - blue) / range) + 360) % 360
    elif maximum == green:
        hue = (60 * ((blue - red) / range) + 120) % 360
    elif maximum == blue:
        hue = (60 * ((red - green) / range) + 240) % 360

    if maximum == 0:
        saturation = 0
    else:
        saturation = (range / maximum) * 100

    value = maximum * 100

    return (hue, saturation, value)


def process_ops_matrix_with_mask(
    str_ops_matrix: t.List[t.List[str]],
    map_hsv_matrix: t.List[t.List[t.Tuple[float, float, float]]],
    source_key: str,
    target_key: str,
) -> t.List[t.List[str]]:
    density_sets = set([val for row in map_hsv_matrix for _, _, val in row])
    source_locations = [
        (j, i)
        for i, row in enumerate(str_ops_matrix)
        for j, item in enumerate(row)
        if item == source_key
    ]

    def get_replacement_locations_for_density(
        density: float,
    ) -> t.List[t.Tuple[int, int]]:
        candidates = [
            xy for xy in source_locations if map_hsv_matrix[xy[1]][xy[0]][2] == density
        ]
        replacement_amount = math.floor((density / 100) * len(candidates))
        return random.sample(candidates, replacement_amount)

    replacements = [
        loc
        for density in density_sets
        for loc in get_replacement_locations_for_density(density)
    ]
    for y, x in replacements:
        str_ops_matrix[x][y] = target_key
    return str_ops_matrix


def get_str_ops_matrix_from_rgb(
    operations_map: t.Dict[str, t.List[float]], rgb_matrix: np.ndarray
) -> t.List[t.List[str]]:
    return [
        [get_operation_from_rgb(operations_map, color) for color in row]
        for row in rgb_matrix
    ]


@click.group()
def cli():
    """Knit pattern generator and processor CLI"""


@cli.command()
@click.argument("input-file", type=click.Path(exists=True))
@click.option(
    "--color-settings",
    type=click.Path(),
    default=os.path.join("input", "color_settings.json"),
    help="Path to JSON file containing knit operations mapped to RGB values",
)
@click.option(
    "--image-width",
    type=int,
    default=None,
    help=(
        "Image width (in pixels). If undefined or None, "
        "the image width will be the same as the width of the input pattern."
    ),
)
@click.option(
    "--image-height",
    type=int,
    default=None,
    help=(
        "Image height (in pixels). If undefined or None, "
        "the image height will be the same as the height of the input pattern."
    ),
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="output",
    help="Output directory to store the images in",
)
def generate_from_source(
    input_file: str,
    color_settings: str,
    image_width: int,
    image_height: int,
    output_dir: str,
):
    """Generates pattern from text or Excel file"""

    operations_map: t.Dict[str, t.List[float]] = get_dictionary_from_file(
        color_settings
    )
    str_ops_matrices, names = extract_pattern_data(input_file)

    for name, str_ops_matrix in zip(names, str_ops_matrices):
        unit_size_x = get_2d_matrix_size_x(str_ops_matrix)
        unit_size_y = get_2d_matrix_size_y(str_ops_matrix)
        current_image_width = image_width or unit_size_x
        current_image_height = image_height or unit_size_y
        out_path = get_output_path(
            basefolder=output_dir,
            subfolder=f"{current_image_width}x{current_image_height}",
            filename=f"{name[:251]}.bmp",
        )
        total_str_ops_matrix = tessellate_with_unit(
            str_ops_matrix, current_image_width, current_image_height
        )
        image = generate_image(operations_map, total_str_ops_matrix)
        image.save(os.path.join(out_path))


@cli.group()
def post_process():
    """Post processes existing pattern"""


@post_process.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--color-settings",
    type=click.Path(),
    default=os.path.join("input", "color_settings.json"),
    help="Path to JSON file containing knit operations mapped to RGB values",
)
@click.option(
    "--density-start",
    type=float,
    default=1.0,
    help="Starting row density",
)
@click.option(
    "--density-end",
    type=float,
    default=0.0,
    help="Ending row density",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="output",
    help="Output directory to store the images in",
)
def per_row(
    filepath: str,
    color_settings: str,
    density_start: float,
    density_end: float,
    output_dir: str,
):
    """Randomly distributes transfer operations per row based on
    density start and end factors"""

    operations_map: t.Dict[str, t.List[float]] = get_dictionary_from_file(
        color_settings
    )
    rgb_matrix = extract_rgb_matrix(filepath)
    str_ops_matrix = get_str_ops_matrix_from_rgb(operations_map, rgb_matrix)

    processed_str_ops_matrix = process_ops_matrix_per_row(
        density_start, density_end, str_ops_matrix, "front_back", "transfer"
    )

    name = get_filename_from_path(filepath)
    out_path = get_output_path(
        basefolder=output_dir,
        subfolder="post-processed",
        filename=f"{name}_edit_{strnow()}.bmp",
    )
    image = generate_image(operations_map, processed_str_ops_matrix)
    image.save(os.path.join(out_path))


@post_process.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--color-settings",
    type=click.Path(),
    default=os.path.join("input", "color_settings.json"),
    help="Path to JSON file containing knit operations mapped to RGB values",
)
@click.option(
    "--transfer-percentage",
    type=int,
    default=40,
    help="Percentage of transfers over selected loop population, default is 40",
)
@click.option(
    "--attractor-u",
    type=float,
    default=0.5,
    help="Position of attractor in pattern U direction within domain (0.0, 1.0)",
)
@click.option(
    "--attractor-v",
    type=float,
    default=0.5,
    help="Position of attractor in pattern V direction within domain (0.0, 1.0)",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="output",
    help="Output directory to store the images in",
)
def with_attractor(
    filepath: str,
    color_settings: str,
    transfer_percentage: int,
    attractor_u: float,
    attractor_v: float,
    output_dir: str,
):
    """Randomly distributes transfer operations in the whole pattern based on
    attractor uv position and transfer replacement percentage"""

    operations_map: t.Dict[str, t.List[float]] = get_dictionary_from_file(
        color_settings
    )
    rgb_matrix = extract_rgb_matrix(filepath)
    str_ops_matrix = get_str_ops_matrix_from_rgb(operations_map, rgb_matrix)
    processed_str_ops_matrix = process_ops_matrix_with_attractor(
        str_ops_matrix,
        transfer_percentage,
        (attractor_u, attractor_v),
        "front_back",
        "transfer",
    )

    name = get_filename_from_path(filepath)
    out_path = get_output_path(
        basefolder=output_dir,
        subfolder="post-processed",
        filename=f"{name}_edit_{strnow()}.bmp",
    )
    image = generate_image(operations_map, processed_str_ops_matrix)
    image.save(os.path.join(out_path))


@post_process.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.argument("mask-path", type=click.Path(exists=True))
@click.option(
    "--color-settings",
    type=click.Path(),
    default=os.path.join("input", "color_settings.json"),
    help="Path to JSON file containing knit operations mapped to RGB values",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="output",
    help="Output directory to store the images in",
)
def with_mask(
    filepath: str,
    mask_path: str,
    color_settings: str,
    output_dir: str,
):
    """Distributes transfer operations in the whole pattern based on mask"""

    operations_map: t.Dict[str, t.List[float]] = get_dictionary_from_file(
        color_settings
    )
    rgb_matrix = extract_rgb_matrix(filepath)
    str_ops_matrix = get_str_ops_matrix_from_rgb(operations_map, rgb_matrix)
    mask_rgb_matrix = extract_rgb_matrix(mask_path)
    mask_hsv_matrix = get_hsv_matrix(mask_rgb_matrix)
    processed_str_ops_matrix = process_ops_matrix_with_mask(
        str_ops_matrix,
        mask_hsv_matrix,
        "front_back",
        "transfer",
    )

    name = get_filename_from_path(filepath)
    out_path = get_output_path(
        basefolder=output_dir,
        subfolder="post-processed",
        filename=f"{name}_edit_{strnow()}.bmp",
    )
    image = generate_image(operations_map, processed_str_ops_matrix)
    image.save(os.path.join(out_path))


if __name__ == "__main__":
    try:
        cli()
    except InvalidPattern:
        click.echo(
            "Invalid pattern(s), please check input file again. "
            "(Attention: number of rows and columns should be the same.)"
        )
    except UnimplementedInputFileFormat:
        click.echo(
            "Input file format not recognised. "
            "Please use a .txt or .xlsx file for your input pattern(s)."
        )
    except EmptyCellFound:
        click.echo("No empty cells are allowed, please update your input pattern(s).")
    except UnknownKnitOperation as exc:
        click.echo(f"Unknown knit operation found: {exc.op}")
    except UnknownColor as exc:
        click.echo(f"Color not found in color settings: {exc.color}")
