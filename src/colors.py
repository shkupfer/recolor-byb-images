from pydantic import BaseModel
import json
from typing import Dict


class Color(BaseModel):
    red: int
    green: int
    blue: int    


class Uniform(BaseModel):
    hat: Dict[str, Color]
    brim_sleeves_collar: Dict[str, Color]
    jersey: Dict[str, Color]


class Team(BaseModel):  
    name: str
    uniform: Uniform


def load_team_colors(team_colors_filename: str) -> Dict[str, Team]:
    with open(team_colors_filename, "r") as team_colors_file:
        team_colors_dct = json.load(team_colors_file)

    teams_colors = {name: Team.parse_obj(team) for name, team in team_colors_dct.items()}
    return teams_colors
