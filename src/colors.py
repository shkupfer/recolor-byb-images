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


with open("data/team_colors.json", "r") as team_colors_file:
    team_colors_dct = json.load(team_colors_file)

TEAMS_COLORS = {name: Team.parse_obj(team) for name, team in team_colors_dct.items()}
BASE_COLORS = TEAMS_COLORS["Color Separated Scheme"]
