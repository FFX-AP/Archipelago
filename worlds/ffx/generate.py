import os
import pkgutil
import struct
import zipfile
import json
import typing

from settings import get_settings
from typing import Optional, Dict
from Options import OptionError
from worlds.AutoWorld import World
from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes, APPatch, APPlayerContainer
from .locations import location_types, get_location_type

if typing.TYPE_CHECKING:
    from .__init__ import FFXWorld
else:
    FFXWorld = object


class FFXContainer(APPlayerContainer):
    game: Optional[str] = "Final Fantasy X"
    patch_file_ending = ".apffx"

    def __init__(self, patch_data: Dict[str, str], base_path: str = "", output_directory: str = "",
                 player: Optional[int] = None, player_name: str = "", server: str = ""):
        self.patch_data = patch_data
        self.file_path = base_path
        container_path = os.path.join(output_directory, base_path + ".apffx")
        super().__init__(container_path, player, player_name, server)

    def write_contents(self, opened_zipfile: zipfile.ZipFile) -> None:
        for filename, yml in self.patch_data.items():
            opened_zipfile.writestr(filename, yml)
        super().write_contents(opened_zipfile)


def options_validation(world: FFXWorld) -> None:
    if world.options.goal_requirement.value == world.options.goal_requirement.option_nemesis:
        if not world.options.capture_sanity.value:
            raise OptionError(f"[Final Fantasy X - '{world.player_name}'] "
                "Goal Requirement: Nemesis cannot be chosen if Capture Sanity is disabled.")
        elif not world.options.creation_rewards.value == world.options.creation_rewards.option_original:
            raise OptionError(f"[Final Fantasy X - '{world.player_name}'] "
                "Goal Requirement: Nemesis cannot be chosen if Creation Rewards is not set to Original Creations.")
        elif not world.options.arena_bosses.value == world.options.arena_bosses.option_original:
            raise OptionError(f"[Final Fantasy X - '{world.player_name}'] "
                "Goal Requirement: Nemesis cannot be chosen if Arena Bosses is not set to Original Creations.")
    elif world.options.creation_rewards.value and not world.options.capture_sanity.value:
        raise OptionError(f"[Final Fantasy X - '{world.player_name}'] "
                "Creation Rewards cannot be enabled if Capture Sanity is disabled.")
    elif world.options.arena_bosses.value and not world.options.capture_sanity.value:
        raise OptionError(f"[Final Fantasy X - '{world.player_name}'] "
                "Arena Bosses cannot be enabled if Capture Sanity is disabled.")
    
    if world.options.goal_requirement.value == world.options.goal_requirement.option_party_members:
        if world.options.required_party_members.value > 8:
            world.options.required_party_members.value = 8


def generate_output(world: FFXWorld, player: int, output_directory: str) -> None:
    seed_data = {
        "SeedId":               world.multiworld.get_out_file_name_base(world.player),
        "GoalRequirement":      world.options.goal_requirement.value,
        "RequiredPartyMembers": world.options.required_party_members.value,
        "RequiredPrimers":      world.options.required_primers.value,
        "APMultiplier":         world.options.ap_multiplier.value,
        "AlwaysSensor":         world.options.always_sensor.value,
        "AlwaysCapture":        world.options.always_capture.value,
        "CaptureDamage":        world.options.capture_damage.value
    }

    locations: dict[str, list[dict[str, int | str] | int] | str] = {x: list() for x in location_types.values()}

    for location in world.multiworld.get_filled_locations(player):
        if location.is_event:
            continue
        if location.item.player != player:
            item_id = 0
        else:
            item_id = location.item.code
        locations[get_location_type(location.address)].append({"location_name": location.name,
                                                               "location_id": location.address & 0x0FFF,
                                                               "item_id": item_id,
                                                               "item_name": location.item.name,
                                                               "player_name": world.multiworld.get_player_name(location.item.player)})

    starting_items: list[int] = list()

    for item in world.multiworld.precollected_items[player]:
        starting_items.append(item.code)
    locations["StartingItems"] = starting_items

    mod_name = world.multiworld.get_out_file_name_base(world.player)
    mod_dir = os.path.join(output_directory, mod_name)
    mod_files = {
        "seed.json"     : json.dumps(seed_data, indent=4),
        "locations.json": json.dumps(locations, indent=4),
    }
    mod = FFXContainer(mod_files, mod_dir, output_directory, world.player,
                       world.multiworld.get_file_safe_player_name(world.player))
    mod.write()