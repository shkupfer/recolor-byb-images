import argparse
import json
import logging
import os
from typing import List

from PIL import Image
import numpy as np

from colors import Color, Uniform, load_team_colors


logging.basicConfig(format='%(message)s')
LOGGER = logging.getLogger("recolor")
LOGGER.setLevel(logging.INFO)

BASE_COLOR_NAME = "Base"


def replace_color(base_data: np.ndarray, old_color: Color, new_color: Color) -> np.ndarray:
    new_player_data = base_data.copy()
    red, green, blue, _alpha = new_player_data.T

    match_color_mask = ((red == old_color.red) & (green == old_color.green) & (blue == old_color.blue))
    new_player_data[..., :-1][match_color_mask.T] = (new_color.red, new_color.green, new_color.blue)

    return new_player_data


def recolor_player_image(
    base_img_data: np.ndarray, old_uniform: Uniform, new_uniform: Uniform, garments: List[str]
) -> np.ndarray:
    # TODO: Restructure Uniform class to make this more elegant...? getattr is an oof
    player_data = base_img_data
    for update_garment_name in garments:
        old_garment = getattr(old_uniform, update_garment_name)
        new_garment = getattr(new_uniform, update_garment_name)
        for old_color, new_color in zip(old_garment.values(), new_garment.values()):
            if old_color and new_color:
                player_data = replace_color(player_data, old_color, new_color)

    return player_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recolor player profile images extracted from Backyard Baseball 2001")
    parser.add_argument(
        "--teams-file",
        "-tf",
        default="sample_data/players_teams.json",
        help="A .json file containing a mapping of player names to color names and base images",
    )
    parser.add_argument(
        "--colors-file",
        "-cf",
        default="sample_data/team_colors.json",
        help="A .json file containing the definition of each color referenced in the teams-file .json",
    )
    parser.add_argument(
        "--base-images-dir",
        "-imgs",
        default="sample_data/player_images/",
        help="Directory containing base images, with filenames corresponding to the teams-file. " +
        "These images should be colored with the base color scheme",
    )
    parser.add_argument("--output-images-dir", "-o", default="sample_data/outputs/")
    parser.add_argument(
        "--names", "-n", nargs="*", help="Recolor only the images of these players." +
        "If not specified, recolor all players' images",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Use this to log more info")

    args = parser.parse_args()

    if args.verbose:
        LOGGER.setLevel(logging.DEBUG)

    with open(args.teams_file, "r") as teams_infile:
        players_teams_colors = json.load(teams_infile)

    if args.names:
        recolor_player_names = args.names
    else:
        # Recolor all players by default
        recolor_player_names = players_teams_colors.keys()
    LOGGER.info(f"Recoloring {len(recolor_player_names)} player images")

    # Load team colors
    teams_colors = load_team_colors(args.colors_file)
    base_colors = teams_colors["Base"]

    os.makedirs(args.output_images_dir, exist_ok=True)

    for player_name in recolor_player_names:
        LOGGER.debug(f"Recoloring player image: {player_name}")
        player_img_colors = players_teams_colors[player_name]
        # Get this player's primary and secondary uniform color schemes from the teams colors mapping
        primary_colors = teams_colors[player_img_colors["primary"]]
        secondary_colors = teams_colors[player_img_colors["secondary"]]

        # Get the player's base image, which have the base color scheme
        base_image_filename = os.path.join(args.base_images_dir, player_img_colors["img_filename"])
        base_image = Image.open(base_image_filename).convert("RGBA")
        base_image_data = np.array(base_image)

        LOGGER.debug(f"Replacing base colors {base_colors.name} with primary colors: {primary_colors.name} and secondary colors: {secondary_colors.name}")
        # First replace the base colors with the player's primary color scheme
        recolored_with_primary = recolor_player_image(
            base_image_data, base_colors.uniform, primary_colors.uniform, garments=["hat", "jersey"]
        )
        # Then replace the base colors with the player's secondary color scheme
        recolored_with_secondary = recolor_player_image(
            recolored_with_primary, base_colors.uniform, secondary_colors.uniform, garments=["brim_sleeves_collar"]
        )

        # Turn the image array into image and save
        final_recolored_image = Image.fromarray(recolored_with_secondary)
        output_filename = os.path.join(args.output_images_dir, player_name + ".png")
        LOGGER.debug(f"Saving recolored {player_name} image to file {output_filename}")
        final_recolored_image.save(output_filename)
