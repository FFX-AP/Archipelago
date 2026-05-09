from BaseClasses import Entrance, ItemClassification, Region, Location, LocationProgressType, CollectionState
import json
import pkgutil
import typing
from typing import Callable, NamedTuple, List

from .locations import FFXLocation, FFXTreasureLocations, FFXPartyMemberLocations, FFXBossLocations, \
    FFXOverdriveLocations, FFXOtherLocations, FFXRecruitLocations, \
    FFXSphereGridLocations, FFXCaptureLocations, FFXLocationData, TreasureOffset, BossOffset, PartyMemberOffset, \
    RecruitOffset, CaptureOffset, OtherOffset, OverdriveOffset
from rule_builder.rules import Rule, Has
from .rules import regionRuleDict, regionBossRuleDict, staticEncounterRuleDict, GoalRequirementRule, PrimerRequirementRule
from .items import party_member_items, key_items, FFXItem

if typing.TYPE_CHECKING:
    from .__init__ import FFXWorld
else:
    FFXWorld = object

class RegionData(dict):
    @property
    def name(self) -> str:
        return self["name"]
    @property
    def id(self) -> int:
        return self["id"]
    @property
    def treasures(self) -> list[int]:
        return self["treasures"]
    @property
    def party_members(self) -> list[int]:
        return self["party_members"]
    @property
    def bosses(self) -> list[int]:
        return self["bosses"]
    @property
    def overdrives(self) -> list[int]:
        return self["overdrives"]
    @property
    def other(self) -> list[int]:
        return self["other"]
    @property
    def recruits(self) -> list[int]:
        return self["recruits"]
    @property
    def captures(self) -> list[int]:
        return self["captures"]
    @property
    def leads_to(self) -> list[int]:
        return self["leads_to"]
    @property
    def rules(self) -> list[str]:
        return self["rules"]


def create_regions(world: FFXWorld, player) -> None:

    def add_locations_by_ids(region: Region, location_ids: list[int], location_data: list[FFXLocationData], location_type: str = ""):
        for id in location_ids:
            locations = [x for x in location_data if x.location_id == id]
            if len(locations) != 1:
                #print(f"Ambiguous or invalid location id {id} ({location_type}) in Region {region.name}. Found {locations}")
                continue
            location = locations[0]

            if location.name in world.skip_locations:
                continue

            if location_type == "Boss" and ((id == 42 and world.options.goal.value == world.options.goal.option_yu_yevon)
                                         or (id == 83 and world.options.goal.value == world.options.goal.option_nemesis )):
                region.add_event(location.name, "Victory", location_type=FFXLocation, item_type=FFXItem)
            else:
                new_location = FFXLocation(player, location.name, location.rom_address, region)
                if location.missable:
                    world.options.exclude_locations.value.add(location.name)
                region.locations.append(new_location)
                all_locations.append(new_location)

    captureDict: dict [int, str]= {
    0:   "Mi'ihen Highroad 1st visit: Pre-Chocobo Eater",                   # Raldo
    1:   "Captures: Djose Highroad & Moonflow",                             # Bunyip
    2:   "Macalania Woods 1st visit: Pre-Spherimorph",                      # Murussu
    3:   "Lake Macalania 1st visit: Pre-Crawler",                           # Mafdet
    4:   "Calm Lands 1st visit: Pre-Defender X",                            # Shred
    5:   "Captures: MRR, Djose Highroad & Moonflow",                        # Gandarewa
    6:   "Thunder Plains 1st visit",                                        # Aerouge
    7:   "Captures: Cavern of the Stolen Fayth & Mt. Gagazet",              # Imp
    8:   "Besaid Island 1st visit",                                         # Dingo
    9:   "Mi'ihen Highroad 1st visit: Pre-Chocobo Eater",                   # Mi'ihen Fang
    10:  "Captures: Djose Highroad & Moonflow",                             # Garm
    11:  "Lake Macalania 1st visit: Pre-Crawler",                           # Snow Wolf
    12:  "Bikanel 1st visit: Post-Zu",                                      # Sand Wolf
    13:  "Calm Lands 1st visit: Pre-Defender X",                            # Skoll
    14:  "Mt. Gagazet 1st visit: Post-Biran and Yenke",                     # Bandersnatch
    15:  "Besaid Island 1st visit",                                         # Water Flan
    16:  "Captures: Miihen Oldroad & MRR",                                  # Thunder Flan
    17:  "Captures: Djose Highroad & Moonflow",                             # Snow Flan
    18:  "Lake Macalania 1st visit: Pre-Crawler",                           # Ice Flan
    19:  "Calm Lands 1st visit: Pre-Defender X",                            # Flame Flan
    20:  "Captures: Mt. Gagazet Caves & Zanarkand",                         # Dark Flan
    21:  "Kilika 1st visit: Pre-Geneaux",                                   # Dinonix
    22:  "Captures: Miihen Oldroad & MRR",                                  # Ipiria
    23:  "Captures: MRR & Djose Highroad",                                  # Raptor
    24:  "Thunder Plains 1st visit",                                        # Melusine
    25:  "Macalania Woods 1st visit: Pre-Spherimorph",                      # Iguion
    26:  "Cavern of the Stolen Fayth 1st visit",                            # Yowie
    27:  "Besaid Island 1st visit",                                         # Condor
    28:  "Djose 1st visit",                                                 # Simurgh
    29:  "Bikanel 1st visit: Post-Zu",                                      # Alcyone
    30:  "Kilika 1st visit: Pre-Geneaux",                                   # Killer Bee
    31:  "Captures: Djose Highroad & Moonflow",                             # Bite Bug
    32:  "Macalania Woods 1st visit: Pre-Spherimorph",                      # Wasp
    33:  "Calm Lands 1st visit: Pre-Defender X",                            # Nebiros
    34:  "Captures: Miihen Highroad & MRR",                                 # Floating Eye
    35:  "Thunder Plains 1st visit",                                        # Buer
    36:  "Lake Macalania 1st visit: Pre-Crawler",                           # Evil Eye
    37:  "Captures: Mt. Gagazet Caves, Zanarkand & Inside Sin",             # Ahriman
    38:  "Kilika 1st visit: Pre-Geneaux",                                   # Ragora
    39:  "Mt. Gagazet 1st visit: Post-Biran and Yenke",                     # Grat
    40:  "Mushroom Rock Road 1st visit: Pre-Sinspawn Gui",                  # Garuda
    41:  "Bikanel 1st visit: Post-Zu",                                      # Zu
    42:  "Bikanel 1st visit: Post-Zu",                                      # Sand Worm
  # 43:  "Unused Arena Index",
    44:  "Cavern of the Stolen Fayth 1st visit",                            # Ghost
    45:  "Mt. Gagazet 1st visit: Post-Seymour Flux",                        # Achelous
    46:  "Mt. Gagazet 1st visit: Post-Seymour Flux",                        # Maelspike
    47:  "Captures: Miihen Highroad & MRR",                                 # Dual Horn
    48:  "Cavern of the Stolen Fayth 1st visit",                            # Valaha
    49:  "Captures: Mt. Gagazet Caves & Zanarkand",                         # Grendel
    50:  "Captures: Miihen Oldroad & MRR",                                  # Vouivre
    51:  "Captures: MRR & Djose Highroad",                                  # Lamashtu
    52:  "Thunder Plains 1st visit",                                        # Kusariqqu
    53:  "Bikanel 1st visit: Post-Zu",                                      # Mushussu
    54:  "Captures: Cavern of the Stolen Fayth & Mt. Gagazet",              # Nidhogg
    55:  "Captures: Calm Lands & Cavern of the Stolen Fayth",               # Malboro
    56:  "Captures: City of Dying Dreams & Omega Ruins",                    # Great Malboro
    57:  "Calm Lands 1st visit: Pre-Defender X",                            # Ogre
    58:  "Captures: Mt. Gagazet Slope & Zanarkand",                         # Bashura
  # 59:  "Unused Arena Index",
    60:  "Mt. Gagazet 1st visit: Post-Seymour Flux",                        # Splasher
    61:  "Kilika 1st visit: Pre-Geneaux",                                   # Yellow Element
    62:  "Mi'ihen Highroad 1st visit: Pre-Chocobo Eater",                   # White Element
    63:  "Mushroom Rock Road 1st visit: Pre-Sinspawn Gui",                  # Red Element
    64:  "Thunder Plains 1st visit",                                        # Gold Element
    65:  "Macalania Woods 1st visit: Pre-Spherimorph",                      # Blue Element
    66:  "Cavern of the Stolen Fayth 1st visit",                            # Dark Element
    67:  "Omega Ruins: Pre-Ultima Weapon",                                  # Black Element
    68:  "Cavern of the Stolen Fayth 1st visit",                            # Epaaj
    69:  "Captures: Mt. Gagazet Caves & Zanarkand",                         # Behemoth
    70:  "Sin: Pre-Seymour Omnis",                                          # Behemoth King
    71:  "Macalania Woods 1st visit: Pre-Spherimorph",                      # Chimera
    72:  "Calm Lands 1st visit: Pre-Defender X",                            # Chimera Brain
    73:  "Captures: Calm Lands & Cavern of the Stolen Fayth",               # Coeurl
    74:  "Omega Ruins: Pre-Ultima Weapon",                                  # Master Coeurl
    75:  "Captures: City of Dying Dreams & Omega Ruins",                    # Demonolith
    76:  "Thunder Plains 1st visit",                                        # Iron Giant
    77:  "Captures: Inside Sin & Omega Ruins Post-Omega Weapon",            # Gemini Sword
    78:  "Captures: Inside Sin & Omega Ruins Post-Omega Weapon",            # Gemini Club
    79:  "Djose 1st visit",                                                 # Basilisk
    80:  "Calm Lands 1st visit: Pre-Defender X",                            # Anacondaur
    81:  "Captures: Inside Sin & Omega Ruins",                              # Adamantoise
    82:  "Omega Ruins: Pre-Ultima Weapon",                                  # Varuna
    83:  "Moonflow 1st visit: Pre-Extractor",                               # Ochu
    84:  "Captures: Mt. Gagazet Caves & Zanarkand",                         # Mandragora
    85:  "Captures: Miihen Highroad & MRR",                                 # Bomb
    86:  "Mt. Gagazet 1st visit: Post-Biran and Yenke",                     # Grenade
    87:  "Thunder Plains 1st visit",                                        # Qactuar
    88:  "Bikanel 1st visit: Post-Zu",                                      # Cactuar
    89:  "Thunder Plains 1st visit",                                        # Larva
    90:  "Sin: Post-Seymour Omnis",                                         # Barbatos
    91:  "Captures: MRR, Djose Highroad & Moonflow",                        # Funguar
    92:  "Cavern of the Stolen Fayth 1st visit",                            # Thorn
    93:  "Sin: Pre-Seymour Omnis",                                          # Exoray
    94:  "Macalania Woods 1st visit: Pre-Spherimorph",                      # Xiphos
    95:  "Omega Ruins: Pre-Ultima Weapon",                                  # Puroboros
    96:  "Omega Ruins: Pre-Ultima Weapon",                                  # Spirit
    97:  "Captures: City of Dying Dreams & Omega Ruins",                    # Wraith
    98:  "Cavern of the Stolen Fayth 1st visit",                            # Tonberry
    99:  "Omega Ruins: Pre-Ultima Weapon",                                  # Master Tonberry
    100: "Omega Ruins: Pre-Ultima Weapon",                                  # Zaurus
    101: "Omega Ruins: Pre-Ultima Weapon",                                  # Halma
    102: "Omega Ruins: Pre-Ultima Weapon",                                  # Floating Death
    103: "Omega Ruins: Pre-Ultima Weapon",                                  # Machea
    }

    # ------------------------------------------------------------------------ #
    #                             Exclude Locations                            #
    # ------------------------------------------------------------------------ #

    # ------------------------------- Blitzball ------------------------------ #
    if not world.options.mini_game_blitzball.value is world.options.mini_game_blitzball.option_up_to_sigil:
        blitzball_treasure_location_ids = []
        blitzball_overdrive_location_ids = []

        up_to = world.options.mini_game_blitzball.value
        up_to_story = world.options.mini_game_blitzball.option_up_to_story
        up_to_world_champion = world.options.mini_game_blitzball.option_up_to_world_champion
        up_to_attack_reels = world.options.mini_game_blitzball.option_up_to_attack_reels
        up_to_status_reels = world.options.mini_game_blitzball.option_up_to_status_reels
        up_to_aurochs_reels = world.options.mini_game_blitzball.option_up_to_aurochs_reels
        up_to_sigil = world.options.mini_game_blitzball.option_up_to_sigil

        if up_to < up_to_sigil:
            blitzball_treasure_location_ids.append(244)  # "Blitzball: Obtain The Jupiter Sigil League Prize (Event)",

        if up_to < up_to_aurochs_reels:
            blitzball_overdrive_location_ids.append(
                23)  # Overdrive: Come 1st in a Blitzball Tournament After Obtaining both Attack & Status Reels (Aurochs Reels)

        if up_to < up_to_status_reels:
            blitzball_overdrive_location_ids.append(
                22)  # Overdrive: Come 1st in a Blitzball League After Obtaining Attack Reels (Status Reels)

        if up_to < up_to_attack_reels:
            blitzball_overdrive_location_ids.append(21)  # Overdrive: Come 1st in a Blitzball Tournament (Attack Reels)

        if up_to < up_to_world_champion:
            blitzball_treasure_location_ids.append(
                93)  # "LUCA: Cafe - Talk to Owner After Placing at Least Third in a Tournament (Chest)" (World Champion),

        if up_to < up_to_story:
            blitzball_treasure_location_ids.append(497)  # "LUCA: Win the Story Blitzball Tournament (Event)",

        for id in blitzball_treasure_location_ids:
            location_name = world.location_id_to_name[id | TreasureOffset]
            world.skip_locations.add(location_name)
        for id in blitzball_overdrive_location_ids:
            location_name = world.location_id_to_name[id | OverdriveOffset]
            world.skip_locations.add(location_name)

    # ------------------------------ Butterflies ----------------------------- #
    if not world.options.mini_game_butterflies:
        butterfly_location_ids = [
            71,  # "MCWO: MP Sphere x1 (Butterfly Minigame Reward before Spherimorph)",
            72,  # "MCWO: Ether x1 (Butterfly Minigame Reward before Spherimorph)",
            280,  # "MCWO: Megalixir x2 (Butterfly Game after defeating Spherimorph)",
            281,  # "MCWO: Elixir x2 (Butterfly Game after defeating Spherimorph)",
            394,  # "MCWO: Teleport Sphere x1 (Butterfly Game after Airship)",
            277,  # "MCWO: Finish Butterfly Minigame (Event)" (Saturn Sigil),
        ]

        for id in butterfly_location_ids:
            location_name = world.location_id_to_name[id | TreasureOffset]
            world.skip_locations.add(location_name)

    # --------------------------- Lightning Dodging -------------------------- #
    if not world.options.mini_game_lightning_dodging is world.options.mini_game_lightning_dodging.option_up_to_200:
        lightning_dodging_location_ids = []

        up_to = world.options.mini_game_lightning_dodging
        up_to_200 = world.options.mini_game_lightning_dodging.option_up_to_200
        up_to_150 = world.options.mini_game_lightning_dodging.option_up_to_150
        up_to_100 = world.options.mini_game_lightning_dodging.option_up_to_100
        up_to_50 = world.options.mini_game_lightning_dodging.option_up_to_50
        up_to_20 = world.options.mini_game_lightning_dodging.option_up_to_20
        up_to_10 = world.options.mini_game_lightning_dodging.option_up_to_10
        up_to_5 = world.options.mini_game_lightning_dodging.option_up_to_5

        if up_to < up_to_200:
            lightning_dodging_location_ids.append(278)  # "THPL: Lightning Dodger - 200 Consecutive Dodges (Event)",

        if up_to < up_to_150:
            lightning_dodging_location_ids.append(194)  # "THPL: Lightning Dodger - 150 Consecutive Dodges (Event)",

        if up_to < up_to_100:
            lightning_dodging_location_ids.append(193)  # "THPL: Lightning Dodger - 100 Consecutive Dodges (Event)",

        if up_to < up_to_50:
            lightning_dodging_location_ids.append(192)  # "THPL: Lightning Dodger - 50 Consecutive Dodges (Event)",

        if up_to < up_to_20:
            lightning_dodging_location_ids.append(191)  # "THPL: Lightning Dodger - 20 Consecutive Dodges (Event)",

        if up_to < up_to_10:
            lightning_dodging_location_ids.append(190)  # "THPL: Lightning Dodger - 10 Consecutive Dodges (Event)",

        if up_to < up_to_5:
            lightning_dodging_location_ids.append(189)  # "THPL: Lightning Dodger - 5 Consecutive Dodges (Event)",

        for id in lightning_dodging_location_ids:
            location_name = world.location_id_to_name[id | TreasureOffset]
            world.skip_locations.add(location_name)

    # ---------------------------- Cactuar Village --------------------------- #
    if not world.options.mini_game_cactuar_village:
        cactuar_village_location_ids = [
            469,  # "BIKA: Shadow Gem x2 (Robeya Minigame Chest)",
            470,  # "BIKA: Shining Gem x1 (Robeya Minigame Chest)",
            471,  # "BIKA: Blessed Gem x1 (Robeya Minigame Chest)",
            472,  # "BIKA: Potion x1 (Cactuar Sidequest Prize)",
            473,  # "BIKA: Elixir x1 (Cactuar Sidequest Prize)",
            474,  # "BIKA: Megalixir x1 (Cactuar Sidequest Prize)",
            475,  # "BIKA: Friend Sphere x1 (Cactuar Sidequest Prize)",
            279,  # "BIKA: Desert - Complete Cactuar Village Quest (Event)", (Mercury Sigil)
        ]

        for id in cactuar_village_location_ids:
            location_name = world.location_id_to_name[id | TreasureOffset]
            world.skip_locations.add(location_name)

    # --------------------------- Chocobo Training --------------------------- #
    if not world.options.mini_game_chocobo_training is world.options.mini_game_chocobo_training.option_up_to_sigil:
        chocobo_training_location_ids = []

        up_to = world.options.mini_game_chocobo_training
        up_to_sigil = world.options.mini_game_chocobo_training.option_up_to_sigil
        up_to_catcher = world.options.mini_game_chocobo_training.option_up_to_catcher
        up_to_hyper_dodger = world.options.mini_game_chocobo_training.option_up_to_hyper_dodger
        up_to_dodger = world.options.mini_game_chocobo_training.option_up_to_dodger
        up_to_wobbly = world.options.mini_game_chocobo_training.option_up_to_wobbly

        if up_to < up_to_sigil:
            chocobo_training_location_ids.append(274)  # "CALM: Catcher chocobo Minigame, Time Under 0.00 (Event)",

        if up_to < up_to_catcher:
            chocobo_training_location_ids.extend([
                340,  # "CALM: Catcher Chocobo Minigame (Event)",
                114,  # "CALM: North - NW Corner, Blocked Until Winning Catcher Chocobo (Event)" (Caladbolg),
            ])

        if up_to < up_to_hyper_dodger:
            chocobo_training_location_ids.append(339)  # "CALM: Hyper Dodger Chocobo Minigame (Event)",

        if up_to < up_to_dodger:
            chocobo_training_location_ids.append(338)  # "CALM: Dodger Chocobo Minigame (Event)",

        if up_to < up_to_wobbly:
            chocobo_training_location_ids.append(337)  # "CALM: Wobbly Chocobo Minigame (Event)",

        for id in chocobo_training_location_ids:
            location_name = world.location_id_to_name[id | TreasureOffset]
            world.skip_locations.add(location_name)

    # ----------------------------- Chocobo Race ----------------------------- #
    if not world.options.mini_game_chocobo_race == world.options.mini_game_chocobo_race.option_up_to_5:
        chocobo_race_location_ids = []

        up_to = world.options.mini_game_chocobo_race
        up_to_cloudy_mirror = world.options.mini_game_chocobo_race.option_up_to_cloudy_mirror
        up_to_1 = world.options.mini_game_chocobo_race.option_up_to_1
        up_to_2 = world.options.mini_game_chocobo_race.option_up_to_2
        up_to_3 = world.options.mini_game_chocobo_race.option_up_to_3
        up_to_4 = world.options.mini_game_chocobo_race.option_up_to_4
        up_to_5 = world.options.mini_game_chocobo_race.option_up_to_5

        if up_to < up_to_5:
            chocobo_race_location_ids.append(419)  # REMI: Win the Chocobo Race With 5 Chests (Event)

        if up_to < up_to_4:
            chocobo_race_location_ids.append(420)  # REMI: Win the Chocobo Race With 4 Chests (Event)

        if up_to < up_to_3:
            chocobo_race_location_ids.append(421)  # REMI: Win the Chocobo Race With 3 Chests (Event)

        if up_to < up_to_2:
            chocobo_race_location_ids.append(418)  # REMI: Win the Chocobo Race With 2 Chests (Event)

        if up_to < up_to_1:
            chocobo_race_location_ids.append(417)  # REMI: Win the Chocobo Race With 1 Chest (Event)

        if up_to < up_to_cloudy_mirror:
            chocobo_race_location_ids.append(176)  # REMI: Win the Chocobo Race (Event)

        for id in chocobo_race_location_ids:
            location_name = world.location_id_to_name[id | TreasureOffset]
            world.skip_locations.add(location_name)

    # ---------------------------- Recruit Sanity ---------------------------- #
    if not world.options.recruit_sanity.value is world.options.recruit_sanity.option_all:
        recruit_location_ids = []
        contracted_ids = [loc.location_id for loc in FFXRecruitLocations[1:36]]
        free_agent_ids = [loc.location_id for loc in [FFXRecruitLocations[0], *FFXRecruitLocations[36:]]]

        including = world.options.recruit_sanity.value

        if including < world.options.recruit_sanity.option_all:
            recruit_location_ids.extend(contracted_ids)

        if including == world.options.recruit_sanity.option_off:
            recruit_location_ids.extend(free_agent_ids)

        for id in recruit_location_ids:
            location_name = world.location_id_to_name[id | RecruitOffset]
            world.skip_locations.add(location_name)

    # ---------------------------- Capture Sanity ---------------------------- #
    if not world.options.capture_sanity.value:
        for location_id, _ in captureDict.items():
            location_name = world.location_id_to_name[location_id | CaptureOffset]
            world.skip_locations.add(location_name)

    # --------------------------- Creation Rewards --------------------------- #
    if not world.options.creation_rewards.value == world.options.creation_rewards.option_original:
        arena_reward_location_ids = [
            424,  # Area Conquest - Capture 1 of Each Besaid Fiend (NPC)
            425,  # Area Conquest - Capture 1 of Each Kilika Fiend (NPC)
            426,  # Area Conquest - Capture 1 of Each Mi'ihen Highraod Fiend (NPC)
            427,  # Area Conquest - Capture 1 of Each MRR Fiend (NPC)
            428,  # Area Conquest - Capture 1 of Each Djose Highroad Fiend (NPC)
            429,  # Area Conquest - Capture 1 of Each Thunder Plains Fiend (NPC)
            430,  # Area Conquest - Capture 1 of Each Macalania Fiend (NPC)
            431,  # Area Conquest - Capture 1 of Each Bikanel Fiend (NPC)
            432,  # Area Conquest - Capture 1 of Each Calm Lands Fiend (NPC)
            433,  # Area Conquest - Capture 1 of Each CotSF Fiend (NPC)
            434,  # Area Conquest - Capture 1 of Each Gagazet Fiend (NPC)
            435,  # Area Conquest - Capture 1 of Each Inside Sin Fiend (NPC)
            436,  # Area Conquest - Capture 1 of Each Omega Ruins Fiend (NPC)
            437,  # Species Conquest - Capture 3 of Each Wolf Fiend (NPC)
            438,  # Species Conquest - Capture 3 of Each Reptile Fiend (NPC)
            439,  # Species Conquest - Capture 5 of Each Bird Fiend (NPC)
            440,  # Species Conquest - Capture 4 of Each Wasp Fiend (NPC)
            441,  # Species Conquest - Capture 4 of Each Imp Fiend (NPC)
            442,  # Species Conquest - Capture 4 of Each Eye Fiend (NPC)
            443,  # Species Conquest - Capture 3 of Each Flan Fiend (NPC)
            444,  # Species Conquest - Capture 3 of Each Elemental Fiend (NPC)
            445,  # Species Conquest - Capture 3 of Each Helm Fiend (NPC)
            446,  # Species Conquest - Capture 4 of Each Drake Fiend (NPC)
            447,  # Species Conquest - Capture 5 of Each Fungi Fiend (NPC)
            448,  # Species Conquest - Capture 5 of Each Bomb Fiend (NPC)
            449,  # Species Conquest - Capture 5 of Each Ruminant Fiend (NPC)
            450,  # Species Conquest - Capture 10 of Each Iron Giant Fiend (NPC)
            451,  # Original Creation - Complete 2 Area Conquests (NPC)
            452,  # Original Creation - Complete 2 Species Conquests (NPC)
            453,  # Original Creation - Complete 6 Area Conquests (NPC)
            454,  # Original Creation - Complete 6 Species Conquests (NPC)
            455,  # Original Creation - Capture 1 of Each Fiend (NPC)
            456,  # Original Creation - Capture 5 of Each Fiend (NPC)
            457,  # Original Creation - Capture 2 of Each Gagazet Underwater Fiend (NPC)
            458,  # Original Creation - Capture 10 of Each Fiend (NPC)
        ]
        match world.options.creation_rewards.value:
            case world.options.creation_rewards.option_area:
                arena_reward_location_ids = arena_reward_location_ids[14:]
            case world.options.creation_rewards.option_species:
                arena_reward_location_ids = arena_reward_location_ids[28:]
        for id in arena_reward_location_ids:
            location_name = world.location_id_to_name[id | TreasureOffset]
            world.skip_locations.add(location_name)

    # ------------------------------ Mars Sigil ------------------------------ #
    if world.options.creation_rewards.value < world.options.creation_rewards.option_area:
        location_name = world.location_id_to_name[276 | TreasureOffset]
        world.skip_locations.add(location_name)

    # ----------------------------- Arena Bosses ----------------------------- #
    if not world.options.arena_bosses.value == world.options.arena_bosses.option_original:
        arena_boss_location_ids = [
            49,  # Stratoavis - Area Conquests
            50,  # Malboro Menace
            51,  # Kottos
            52,  # Coeurlregina
            53,  # Jormungand
            54,  # Cactuar King
            55,  # Espada
            56,  # Abyss Worm
            57,  # Chimerageist
            58,  # Don Tonberry
            59,  # Catoblepas
            60,  # Abaddon
            61,  # Vorban
            62,  # Fenrir - Species Conquests
            63,  # Ornitholestes
            64,  # Pteryx
            65,  # Hornet
            66,  # Vidatu
            67,  # One-Eye
            68,  # Jumbo Flan
            69,  # Nega Elemental
            70,  # Tanket
            71,  # Fafnir
            72,  # Sleep Sprout
            73,  # Bomb King
            74,  # Juggernaut
            75,  # Ironclad
            76,  # Earth Eater - Original Creations
            77,  # Greater Sphere
            78,  # Catastrophe
            79,  # Th'uban
            80,  # Neslug
            81,  # Ultima Buster
            82,  # Shinryu
            83,  # Nemesis
        ]
        match world.options.arena_bosses.value:
            case world.options.arena_bosses.option_area:
                arena_boss_location_ids = arena_boss_location_ids[13:]
            case world.options.arena_bosses.option_species:
                arena_boss_location_ids = arena_boss_location_ids[27:]
        for id in arena_boss_location_ids:
            location_name = world.location_id_to_name[id | BossOffset]
            world.skip_locations.add(location_name)
        location_name = world.location_id_to_name[496 | TreasureOffset]
        world.skip_locations.add(location_name)

    # ----------------------------- Super Bosses ----------------------------- #
    if not world.options.super_bosses.value:
        super_boss_location_ids = [
            2,  # "Besaid: Dark Valefor"
            19,  # "Bikanel: Dark Ifrit"
            13,  # "Thunder Plains: Dark Ixion"
            18,  # "Lake Macalania: Dark Shiva"
            38,  # "Zanarkand: Dark Bahamut"
            31,  # "Cavern of the Stolen Fayth: Dark Yojimbo"
            45,  # "Mushroom Rock Road: Dark Mindy"
            46,  # "Mushroom Rock Road: Dark Sandy"
            47,  # "Mushroom Rock Road: Dark Cindy"
            34,  # "Gagazet (Outside): Dark Anima"
            # 25, # "Airship: Penance"
            44,  # "Omega Ruins: Omega Weapon"
        ]
        super_boss_treasure_ids = [
            332,  # OMGR: Omega Boss Arena (Chest)
        ]
        super_boss_other_ids = [
            27,  # Jecht Sphere 2 - Requires Dark Valefor
        ]
        for id in super_boss_location_ids:
            location_name = world.location_id_to_name[id | BossOffset]
            world.skip_locations.add(location_name)
        for id in super_boss_treasure_ids:
            location_name = world.location_id_to_name[id | TreasureOffset]
            world.skip_locations.add(location_name)
        for id in super_boss_other_ids:
            location_name = world.location_id_to_name[id | OtherOffset]
            world.skip_locations.add(location_name)

    # ---------------------------- Jecht's Spheres --------------------------- #
    if not world.options.jecht_spheres.value:
        jecht_sphere_location_ids = [
            27,  # Jecht Sphere 2
            28,  # Jecht Sphere 3
            29,  # Jecht Sphere 4
            30,  # Jecht Sphere 5
            31,  # Jecht Sphere 6
            32,  # Auron Sphere
            33,  # Jecht Sphere 7
            34,  # Jecht Sphere 8
            35,  # Braska Sphere
        ]
        for id in jecht_sphere_location_ids:
            location_name = world.location_id_to_name[id | OtherOffset]
            world.skip_locations.add(location_name)
        location_name = world.location_id_to_name[177 | TreasureOffset]
        world.skip_locations.add(location_name)

    # ------------------------------ Overdrives ------------------------------ #
    # Tidus
    if not world.options.tidus_overdrives.value == world.options.tidus_overdrives.option_up_to_blitz_ace:
        overdrive_location_ids = []

        up_to = world.options.tidus_overdrives.value
        slice_and_dice = world.options.tidus_overdrives.option_up_to_slice_and_dice
        energy_rain = world.options.tidus_overdrives.option_up_to_energy_rain
        blitz_ace = world.options.tidus_overdrives.option_up_to_blitz_ace

        if up_to < blitz_ace:
            overdrive_location_ids.append(3)  # Overdrive: Use Tidus's Overdrive 80 Times (Blitz Ace)

        if up_to < energy_rain:
            overdrive_location_ids.append(2)  # Overdrive: Use Tidus's Overdrive 30 Times (Energy Rain)

        if up_to < slice_and_dice:
            overdrive_location_ids.append(1)  # Overdrive: Use Tidus's Overdrive 10 Times (Slice and Dice)

        for id in overdrive_location_ids:
            location_name = world.location_id_to_name[id | OverdriveOffset]
            world.skip_locations.add(location_name)

    # Kimahri
    if not world.options.kimahri_ronso_rages.value:
        overdrive_location_ids = [
            # 8,  # Ronso Rage: Jump
            9,  # Ronso Rage: Use Lancet to Learn Fire Breath
            10,  # Ronso Rage: Use Lancet to Learn Seed Cannon
            11,  # Ronso Rage: Use Lancet to Learn Self Destruct
            12,  # Ronso Rage: Use Lancet to Learn Thrust Kick
            13,  # Ronso Rage: Use Lancet to Learn Stone Breath
            14,  # Ronso Rage: Use Lancet to Learn Aqua Breath
            15,  # Ronso Rage: Use Lancet to Learn Doom
            16,  # Ronso Rage: Use Lancet to Learn White Wind
            17,  # Ronso Rage: Use Lancet to Learn Bad Breath
            18,  # Ronso Rage: Use Lancet to Learn Mighty Guard
            19,  # Ronso Rage: Use Lancet to Learn Nova
        ]
        for id in overdrive_location_ids:
            location_name = world.location_id_to_name[id | OverdriveOffset]
            world.skip_locations.add(location_name)
            # Nova
    if not world.options.arena_bosses.value == world.options.arena_bosses.option_original and not world.options.super_bosses.value:
        nova_location = world.location_id_to_name[19 | OverdriveOffset]
        world.skip_locations.add(nova_location)

    # --------------------------- Contest of Aeons --------------------------- #
    if world.options.skip_contest_of_aeons.value:
        aeons_location = world.location_id_to_name[41 | BossOffset]
        world.skip_locations.add(aeons_location)

    # --------------------------------- Goals -------------------------------- #
    if world.options.goal.value == world.options.goal.option_yu_yevon:
        bfa_location = world.location_id_to_name[40 | BossOffset]
        aeons_location = world.location_id_to_name[41 | BossOffset]
        world.skip_locations.add(bfa_location)
        world.skip_locations.add(aeons_location)

    # ------------------------------------------------------------------------ #
    #                              Region Creation                             #
    # ------------------------------------------------------------------------ #
    
    menu_region = Region("Menu", player, world.multiworld)
    world.multiworld.regions.append(menu_region)

    region_file = pkgutil.get_data(__name__, "data/regions.json")
    #region_data_list = [RegionData(x) for x in json.loads(region_file)]
    region_data_list = json.loads(region_file)
    region_data_list = [RegionData(x) for x in region_data_list]

    region_dict: dict[int, Region] = dict()
    region_rules: dict[int, list[str]] = dict()

    all_locations = []

    # ------------------------ Add Locations by Region ----------------------- #
    for region_data in region_data_list:
        new_region = Region(region_data.name, player, world.multiworld)
        region_dict[region_data.id] = new_region
        world.multiworld.regions.append(new_region)
        if len(region_data.rules) > 0:
            region_rules[region_data.id] = region_data.rules

        add_locations_by_ids(new_region, region_data.treasures, FFXTreasureLocations, "Treasure")

        add_locations_by_ids(new_region, region_data.party_members, FFXPartyMemberLocations, "Party Member")

        add_locations_by_ids(new_region, region_data.bosses, FFXBossLocations, "Boss")

        add_locations_by_ids(new_region, region_data.overdrives, FFXOverdriveLocations, "Overdrive")

        add_locations_by_ids(new_region, region_data.other, FFXOtherLocations, "Other")

        add_locations_by_ids(new_region, region_data.recruits, FFXRecruitLocations, "Recruit")

    for location_id, region_name in captureDict.items():
        add_locations_by_ids(world.get_region(region_name), [location_id], FFXCaptureLocations, "Capture")

    for location_data in FFXOverdriveLocations[:6]:
        if location_data.name in world.skip_locations:
            continue
        overdrive_location = FFXLocation(player, location_data.name, location_data.rom_address, menu_region)
        menu_region.locations.append(overdrive_location)

    # ---------------------------- Entrance Rules ---------------------------- #
    for region_data in region_data_list:
        curr_region = region_dict[region_data.id]
        for region_id in region_data.leads_to:
            other_region = region_dict[region_id]
            rules = region_rules.get(region_id)
            entrance: Entrance = curr_region.connect(other_region)
            new_rule: Rule = None
            if rules is not None:
                for rule in rules:
                    regionRule: Rule | None = regionRuleDict.get(rule, 
                        regionBossRuleDict.get(rule, 
                        staticEncounterRuleDict.get(rule, None)))
                    if new_rule is not None:
                        new_rule &= regionRule
                    else:
                        new_rule = regionRule
                world.set_rule(entrance, new_rule)

    top_level_regions: list[tuple[Region, Entrance]] = []
    for region_id, other_region in region_dict.items():
        if len(other_region.entrances) == 0:
            rules = region_rules.get(region_id)
            menu_entrance: Entrance = menu_region.connect(other_region)
            new_rule: Rule = None
            if rules is not None:
                for rule in rules:
                    regionRule: Rule | None = regionRuleDict.get(rule, 
                        regionBossRuleDict.get(rule, 
                        staticEncounterRuleDict.get(rule, None)))
                    if new_rule is not None:
                        new_rule &= regionRule
                    else:
                        new_rule = regionRule
                world.set_rule(menu_entrance, new_rule)
            top_level_regions.append((other_region, menu_entrance))


    if world.options.mini_game_chocobo_training < world.options.mini_game_chocobo_training.option_up_to_wobbly:
        # Change Remiem access from Wobbly Chocobo to Post-Defender X
        calm_lands_to_remiem = world.get_region("Remiem Temple").entrances[0]
        new_parent = world.get_region("Calm Lands 1st visit: Post-Defender X")
        calm_lands_to_remiem.parent_region.exits.remove(calm_lands_to_remiem)
        calm_lands_to_remiem.parent_region = new_parent
        new_parent.exits.append(calm_lands_to_remiem)

    # ------------------------------------------------------------------------ #
    #                             Victory Condition                            #
    # ------------------------------------------------------------------------ #

    match world.options.goal.value:
        case world.options.goal.option_yu_yevon:
            goal_location = world.get_location(world.location_id_to_name[42 | BossOffset])
        case world.options.goal.option_nemesis:
            goal_location = world.get_location(world.location_id_to_name[83 | BossOffset])

    world.set_rule(goal_location, GoalRequirementRule() & PrimerRequirementRule())


    world.set_completion_rule(Has("Victory"))   
