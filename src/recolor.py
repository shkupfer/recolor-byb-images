import argparse
import json
import os
from typing import List

from PIL import Image
import numpy as np

from colors import Color, Uniform, TEAMS_COLORS, BASE_COLORS


def replace_color(base_data: np.ndarray, old_color: Color, new_color: Color) -> np.ndarray:
    new_player_data = base_data.copy()
    red, green, blue, _alpha = new_player_data.T

    match_color_mask = ((red == old_color.red) & (green == old_color.green) & (blue == old_color.blue))
    new_player_data[..., :-1][match_color_mask.T] = (new_color.red, new_color.green, new_color.blue)

    return new_player_data


def recolor_player_image(
    base_img_data: np.ndarray, old_uniform: Uniform, new_uniform: Uniform, garments: List[str]
) -> np.ndarray:
    # TODO: Restructure Uniform class to make this more elegant...?
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
        default="data/players_teams_colors.json",
        help="A .json file containing a mapping of player names to color names and base images",
    )
    # TODO: Have colors.py load the colors into TEAMS_COLORS based on this arg
    # parser.add_argument(
    #     "--colors-file",
    #     "-cf",
    #     required=True,
    #     help="A .json file containing the definition of each color referenced in the teams-file .json",
    # )
    parser.add_argument("--base-images-dir", "-imgs", default="data/player_images/", help="TODO fill this in")
    parser.add_argument("--output-images-dir", "-o", default="data/outputs/")
    which_players_arg_grp = parser.add_mutually_exclusive_group(required=True)
    which_players_arg_grp.add_argument("--all", "-a", action="store_true", help="Recolor all players' images")
    which_players_arg_grp.add_argument("--names", "-n", nargs="*", help="Recolor only the images of these players")

    args = parser.parse_args()

    with open(args.teams_file, "r") as teams_infile:
        players_teams_colors = json.load(teams_infile)
    # with open(args.colors_file, "r") as colors_infile:
    #     colors = json.load(colors_infile)

    if args.all:
        recolor_player_names = players_teams_colors.keys()
    else:
        recolor_player_names = args.names

    for player_name in recolor_player_names:
        player_img_colors = players_teams_colors[player_name]
        primary_colors = TEAMS_COLORS[player_img_colors["primary"]]
        secondary_colors = TEAMS_COLORS[player_img_colors["secondary"]]

        base_image_filename = os.path.join(args.base_images_dir, player_img_colors["img_filename"])
        base_image = Image.open(base_image_filename).convert("RGBA")
        base_image_data = np.array(base_image)

        recolored_with_primary = recolor_player_image(
            base_image_data, BASE_COLORS.uniform, primary_colors.uniform, garments=["hat", "jersey"]
        )
        recolored_with_secondary = recolor_player_image(
            recolored_with_primary, BASE_COLORS.uniform, secondary_colors.uniform, garments=["brim_sleeves_collar"]
        )

        final_recolored_image = Image.fromarray(recolored_with_secondary)
        output_filename = os.path.join(args.output_images_dir, player_name + ".png")
        final_recolored_image.save(output_filename)
