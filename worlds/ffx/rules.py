import typing
from collections import Counter
from dataclasses import dataclass
from typing_extensions import override

from BaseClasses import CollectionState, Location, Region
from rule_builder.rules import Rule, CanReachLocation, CanReachRegion, Has, HasAll, HasAny, HasFromListUnique, True_, False_
# from rule_builder import set
from worlds.generic.Rules import CollectionRule
from . import key_items
from .items import character_names, stat_abilities, item_to_stat_value, aeon_names, party_member_items, region_unlock_items, equipItemOffset
from .locations import TreasureOffset, OtherOffset, BossOffset, PartyMemberOffset, CaptureOffset, OverdriveOffset

if typing.TYPE_CHECKING:
    from .__init__ import FFXWorld
else:
    FFXWorld = object

world_battle_levels: dict[str, int] = {
"Monster Arena":               0,
"Guadosalam":                  0,
"Baaj Temple":                 1,
"Besaid":                      2,
"Kilika":                      3,
"Luca":                        4,
"Mi'ihen Highroad":            5,
"Mushroom Rock Road":          6,
"Djose":                       7,
"Moonflow":                    8,
"Thunder Plains":              9,
"Macalania":                  10,
"Bikanel":                    11,
"Airship":                    12,
"Bevelle":                    12,
"Calm Lands":                 13,
"Cavern of the Stolen Fayth": 13,
"Mt. Gagazet":                14,
"Zanarkand Ruins":            15,
"Sin":                        16,
"Omega Ruins":                17,
}

region_to_first_visit: dict[str, str] = {
"Baaj Temple":                "Baaj Temple 1st visit",
"Besaid":                     "Besaid Island 1st visit",
"Kilika":                     "Kilika 1st visit: Pre-Geneaux",
"Luca":                       "Luca 1st visit: Pre-Oblitzerator",
"Mi'ihen Highroad":           "Mi'ihen Highroad 1st visit: Pre-Chocobo Eater",
"Mushroom Rock Road":         "Mushroom Rock Road 1st visit: Pre-Sinspawn Gui",
"Djose":                      "Djose 1st visit",
"Moonflow":                   "Moonflow 1st visit: Pre-Extractor",
"Guadosalam":                 "Guadosalam 1st visit",
"Thunder Plains":             "Thunder Plains 1st visit",
"Macalania":                  "Macalania Woods 1st visit: Pre-Spherimorph",
"Bikanel":                    "Bikanel 1st visit: Pre-Zu",
"Bevelle":                    "Bevelle 1st visit: Pre-Isaaru",
"Calm Lands":                 "Calm Lands 1st visit: Pre-Defender X",
"Monster Arena":              "Monster Arena",  
"Cavern of the Stolen Fayth": "Cavern of the Stolen Fayth 1st visit",
"Mt. Gagazet":                "Mt. Gagazet 1st visit: Pre-Biran and Yenke",
"Zanarkand Ruins":            "Zanarkand Ruins 1st visit: Pre-Spectral Keeper",
"Sin":                        "Sin: Pre-Seymour Omnis",
"Airship":                    "Airship 1st visit: Pre-Evrae",
"Omega Ruins":                "Omega Ruins: Pre-Ultima Weapon",
}

# ---------------------------------------------------------------------------- #
#                                 Custom Rules                                 #
# ---------------------------------------------------------------------------- #

@dataclass()
class AbilityRule(Rule[FFXWorld], game="Final Fantasy X"):
    ability_name: str
    character_name: str | None

    @override
    def _instantiate(self, world: FFXWorld) -> Rule.Resolved:
        if world.options.sphere_grid_randomization.value:
            if self.character_name is not None:
                return Has(f"{self.character_name} Ability: {self.ability_name}").resolve(world)
            else:
                return HasAny(HasAll([f"{name} Ability: {self.ability_name}", f"Party Member: {name}"]) for name in character_names).resolve(world)
        else:
            return True_().resolve(world)


@dataclass()
class CanReachMinimumLocationRule(Rule[FFXWorld], game="Final Fantasy X"):
    """A rule that checks if a required number of locations are reachable from a given list of locations"""
    locations: list[Location]
    locations_required: int

    @override
    def _instantiate(self, world: FFXWorld) -> Rule.Resolved:
        sum = 0
        for location in self.locations:
            if CanReachLocation(location.name) is not None:
                sum += 1
                if sum >= self.locations_required:
                    return True_().resolve(world)
        return False_().resolve(world)


@dataclass()
class CanReachMinimumRegionRule(Rule[FFXWorld], game="Final Fantasy X"):
    """A rule that checks if a required number of regions are reachable from a given list of regions"""
    regions: list[Region]
    regions_required: int

    @override
    def _instantiate(self, world: FFXWorld) -> Rule.Resolved:
        sum = 0
        for region in self.regions:
            if CanReachRegion(region.name) is not None:
                sum += 1
                if sum >= self.regions_required:
                    return True_().resolve(world)
        return False_().resolve(world)


@dataclass()
class GoalRequirementRule(Rule[FFXWorld], game="Final Fantasy X"):

    @override
    def _instantiate(self, world: FFXWorld) -> Rule.Resolved:
        match world.options.goal_requirement.value:
            case world.options.goal_requirement.option_none:
                return True_().resolve(world)
            case world.options.goal_requirement.option_party_members:
                print([character.itemName for character in party_member_items[:8]])
                return HasFromListUnique(*[character.itemName for character in party_member_items[:8]], count=min(world.options.required_party_members.value, 8)).resolve(world)
            case world.options.goal_requirement.option_party_members_and_aeons:
                return HasFromListUnique(*[character.itemName for character in party_member_items], count=world.options.required_party_members.value).resolve(world)
            case world.options.goal_requirement.option_pilgrimage:
                return (
                    CanReachLocation(world.location_id_to_name[ 8 | PartyMemberOffset]) &   # Valefor
                    CanReachLocation(world.location_id_to_name[ 9 | PartyMemberOffset]) &   # Ifrit
                    CanReachLocation(world.location_id_to_name[10 | PartyMemberOffset]) &   # Ixion
                    CanReachLocation(world.location_id_to_name[11 | PartyMemberOffset]) &   # Shiva
                    CanReachLocation(world.location_id_to_name[12 | PartyMemberOffset]) &   # Bahamut
                    CanReachLocation(world.location_id_to_name[37 | BossOffset       ])     # Yunalesca
                ).resolve(world)
            case world.options.goal_requirement.option_nemesis:
                return CanReachLocation(world.location_id_to_name[83 | BossOffset]).resolve(world)  # Nemesis


@dataclass()
class LogicDifficultyRule(Rule[FFXWorld], game="Final Fantasy X"):
    difficulty: int

    @override
    def _instantiate(self, world: FFXWorld) -> Rule.Resolved:
        appropriate_level_regions = [other_region for other_region, other_level in world_battle_levels.items() if
                                    self.difficulty >= other_level >= self.difficulty - world.options.logic_difficulty.value]
        can_reach_region: Rule = None
        for other_region in appropriate_level_regions:
            if can_reach_region is not None:
                can_reach_region |= CanReachRegion(region_to_first_visit[other_region])
            else:
                can_reach_region = CanReachRegion(region_to_first_visit[other_region])
        
        if can_reach_region is not None:
            return can_reach_region.resolve(world)
        else:
            return False_().resolve(world)
    

@dataclass()
class MinPartyRule(Rule[FFXWorld], game="Final Fantasy X"):
    num_characters: int

    @override
    def _instantiate(self, world: FFXWorld) -> Rule.Resolved:
        return HasFromListUnique(*[f"Party Member: {name}" for name in character_names], 
                                 count=self.num_characters).resolve(world)
    

@dataclass()
class MinSummonRule(Rule[FFXWorld], game="Final Fantasy X"):
    num_aeons: int

    @override
    def _instantiate(self, world: FFXWorld) -> Rule.Resolved:
        return (HasFromListUnique(*[f"Party Member: {name}" for name in aeon_names], count=self.num_aeons) &
                Has(f"Party Member: Yuna")).resolve(world)
                

@dataclass()
class MinSwimmerRule(Rule[FFXWorld], game="Final Fantasy X"):
    num_characters: int
    
    @override
    def _instantiate(self, world: FFXWorld) -> Rule.Resolved:
        return HasFromListUnique(*[f"Party Member: {name}" for name in ["Tidus", "Wakka", "Rikku"]], 
                                 count=self.num_characters).resolve(world)
        

@dataclass()
class NotRule(Rule[FFXWorld], game="Final Fantasy X"):
    rule: Rule
    
    @override
    def _instantiate(self, world: FFXWorld) -> Rule.Resolved:
        if self.rule.resolve(world):
            return False_().resolve(world)
        else:
            return True_().resolve(world)


@dataclass()
class PrimerRequirementRule(Rule[FFXWorld], game="Final Fantasy X"):

    @override
    def _instantiate(self, world: FFXWorld) -> Rule.Resolved:
        if world.options.required_primers.value > 0:
            return Has("Progressive Al Bhed Primer", count=world.options.required_primers.value).resolve(world)
        else:
            return True_().resolve(world)


@dataclass()
class RangedRule(Rule[FFXWorld], game="Final Fantasy X"):    
    
    @override
    def _instantiate(self, world: FFXWorld) -> Rule.Resolved:
        return (HasFromListUnique(*[f"Party Member: {name}" for name in ["Wakka", "Lulu"]], count=1) | 
                    (Has("Party Member: Yuna") & HasFromListUnique(*[f"Party Member: {name}" for name in aeon_names[:6]], count=1))).resolve(world)


@dataclass()
class RegionAccessRule(Rule[FFXWorld], game="Final Fantasy X"):
    region_name: str

    @override
    def _instantiate(self, world: FFXWorld) -> Rule.Resolved:
        region_level: int = world_battle_levels[self.region_name]
        if region_level < 5:
            return Has(f"Region: {self.region_name}").resolve(world)
        else:
            appropriate_level_regions = [other_region for other_region, other_level in world_battle_levels.items()
                                        if  other_region != self.region_name 
                                        and region_level > other_level >= region_level - world.options.logic_difficulty.value
                                        ]
            can_reach_region: Rule = None
            for other_region in appropriate_level_regions:
                if can_reach_region is not None:
                    can_reach_region |= CanReachRegion(region_to_first_visit[other_region])
                else:
                    can_reach_region = CanReachRegion(region_to_first_visit[other_region])
                
            if can_reach_region is not None:
                return (Has(f"Region: {self.region_name}") & can_reach_region).resolve(world)
            else:
                return False_().resolve(world)


@dataclass()
class StatTotalRule(Rule[FFXWorld], game="Final Fantasy X"):
    num_party_members: int
    stat_total: int

    @override
    def _instantiate(self, world: FFXWorld) -> Rule.Resolved:
        player_prog_items = world.multiworld.state.prog_items[world.player]
        totals = Counter()
        for item, count in player_prog_items.items():
            if item in stat_abilities:
                character, value = item_to_stat_value[item]
                totals[character] += value*count

        if len([total for total in totals.values() if total > self.stat_total]) >= self.num_party_members:
            return True_().resolve(world)
        else:
            return False_().resolve(world)

# ---------------------------------------------------------------------------- #
#                               Rule Dictionaries                              #
# ---------------------------------------------------------------------------- #

regionRuleDict: dict[str, Rule] = {
    "Baaj Temple":                RegionAccessRule("Baaj Temple"),
    "Besaid":                     RegionAccessRule("Besaid"),
    "Kilika":                     RegionAccessRule("Kilika"),
    "Luca":                       RegionAccessRule("Luca"),
    "Mi'ihen Highroad":           RegionAccessRule("Mi'ihen Highroad"),
    "Mushroom Rock Road":         RegionAccessRule("Mushroom Rock Road"),
    "Djose":                      RegionAccessRule("Djose"),
    "Moonflow":                   RegionAccessRule("Moonflow"),
    "Guadosalam":                 RegionAccessRule("Guadosalam"),
    "Thunder Plains":             RegionAccessRule("Thunder Plains"),
    "Macalania":                  RegionAccessRule("Macalania"),
    "Bikanel":                    RegionAccessRule("Bikanel"),
    "Bevelle":                    RegionAccessRule("Bevelle"),
    "Calm Lands":                 RegionAccessRule("Calm Lands"),
    "Monster Arena":              RegionAccessRule("Monster Arena"),
    "Cavern of the Stolen Fayth": RegionAccessRule("Cavern of the Stolen Fayth"),
    "Mt. Gagazet":                RegionAccessRule("Mt. Gagazet"),
    "Zanarkand Ruins":            RegionAccessRule("Zanarkand Ruins"),
    "Sin":                        RegionAccessRule("Sin"),
    "Airship":                    RegionAccessRule("Airship"),
    "Omega Ruins":                RegionAccessRule("Omega Ruins"),
}

regionBossRuleDict: dict[str, Rule] = {
    "Sin Fin":             LogicDifficultyRule( 2) & MinPartyRule  (3) & RangedRule(),
    "Sinspawn Echuilles":  LogicDifficultyRule( 2) & MinSwimmerRule(2),
    "Sinspawn Geneaux":    LogicDifficultyRule( 3) & MinPartyRule  (3),
    "Oblitzerator":        LogicDifficultyRule( 4) & MinPartyRule  (3),
    "Chocobo Eater":       LogicDifficultyRule( 5) & MinPartyRule  (3),
    "Sinspawn Gui":        LogicDifficultyRule( 6) & MinPartyRule  (3),
    "Extractor":           LogicDifficultyRule( 8) & MinSwimmerRule(2),
    "Spherimorph":         LogicDifficultyRule(10) & MinPartyRule  (3),
    "Crawler":             LogicDifficultyRule(10) & MinPartyRule  (3),
    "Seymour/Anima":       LogicDifficultyRule(10) & MinPartyRule  (3),
    "Wendigo":             LogicDifficultyRule(10) & MinPartyRule  (3),
    "Zu":                  LogicDifficultyRule(11) & MinPartyRule  (3),
    "Evrae":               LogicDifficultyRule(12) & MinPartyRule  (3),
    "Isaaru":              LogicDifficultyRule(12) & MinSummonRule (2),
    "Evrae Altana":        LogicDifficultyRule(12) & MinSwimmerRule(3),
    "Seymour Natus":       LogicDifficultyRule(12) & MinPartyRule  (3),
    "Defender X":          LogicDifficultyRule(13) & MinPartyRule  (3),
    "Biran and Yenke":     LogicDifficultyRule(14) & Has("Party Member: Kimahri"),
    "Seymour Flux":        LogicDifficultyRule(14) & MinPartyRule  (3),
    "Sanctuary Keeper":    LogicDifficultyRule(14) & MinPartyRule  (3),
    "Spectral Keeper":     LogicDifficultyRule(15) & MinPartyRule  (3),
    "Yunalesca":           LogicDifficultyRule(15) & MinPartyRule  (3),
    "Geosgaeno":           LogicDifficultyRule(15) & MinSwimmerRule(3),
    "Airship Sin":         LogicDifficultyRule(16) & MinPartyRule  (3),
    "Overdrive Sin":       LogicDifficultyRule(16) & MinPartyRule  (3),
    "Seymour Omnis":       LogicDifficultyRule(16) & MinPartyRule  (3),
    "Braska's Final Aeon": LogicDifficultyRule(16) & MinPartyRule  (3),
    "Ultima Weapon":       LogicDifficultyRule(17) & MinPartyRule  (3),
    "Omega Weapon":        LogicDifficultyRule(18) & MinPartyRule  (3),
    "Nemesis":             LogicDifficultyRule(18) & MinPartyRule  (3),
}

staticEncounterRuleDict: dict[str, Rule] = {
    "Belgemine":    MinSummonRule(2),
    "Ronso Rage":   Has("Party Member: Kimahri")
}

arenaBossRuleDict: dict[int, Rule] = {
    49: LogicDifficultyRule(17) & MinPartyRule  (3), # Stratoavis
    50: LogicDifficultyRule(17) & MinPartyRule  (3), # Malboro Menace
    51: LogicDifficultyRule(17) & MinPartyRule  (3), # Kottos
    52: LogicDifficultyRule(17) & MinPartyRule  (3), # Coeurlregina
    53: LogicDifficultyRule(17) & MinPartyRule  (3), # Jormungand
    54: LogicDifficultyRule(17) & MinPartyRule  (3), # Cactuar King
    55: LogicDifficultyRule(17) & MinPartyRule  (3), # Espada
    56: LogicDifficultyRule(17) & MinPartyRule  (3), # Abyss Worm
    57: LogicDifficultyRule(17) & MinPartyRule  (3), # Chimerageist
    58: LogicDifficultyRule(17) & MinPartyRule  (3), # Don Tonberry
    59: LogicDifficultyRule(17) & MinPartyRule  (3), # Catoblepas
    60: LogicDifficultyRule(17) & MinPartyRule  (3), # Abaddon
    61: LogicDifficultyRule(17) & MinPartyRule  (3), # Vorban

    62: LogicDifficultyRule(17) & MinPartyRule  (3), # Fenrir
    63: LogicDifficultyRule(17) & MinPartyRule  (3), # Ornitholestes
    64: LogicDifficultyRule(17) & MinPartyRule  (3), # Pteryx
    65: LogicDifficultyRule(17) & MinPartyRule  (3), # Hornet
    66: LogicDifficultyRule(17) & MinPartyRule  (3), # Vidatu
    67: LogicDifficultyRule(17) & MinPartyRule  (3), # One-Eye
    68: LogicDifficultyRule(17) & MinPartyRule  (3), # Jumbo Flan
    69: LogicDifficultyRule(17) & MinPartyRule  (3), # Nega Elemental
    70: LogicDifficultyRule(17) & MinPartyRule  (3), # Tanket
    71: LogicDifficultyRule(17) & MinPartyRule  (3), # Fafnir
    72: LogicDifficultyRule(17) & MinPartyRule  (3), # Sleep Sprout
    73: LogicDifficultyRule(17) & MinPartyRule  (3), # Bomb King
    74: LogicDifficultyRule(17) & MinPartyRule  (3), # Juggernaut
    75: LogicDifficultyRule(17) & MinPartyRule  (3), # Ironclad
    
    76: LogicDifficultyRule(18) & MinPartyRule  (3), # Earth Eater
    77: LogicDifficultyRule(18) & MinPartyRule  (3), # Greater Sphere
    78: LogicDifficultyRule(18) & MinPartyRule  (3), # Catastrophe
    79: LogicDifficultyRule(18) & MinPartyRule  (3), # Th'uban
    80: LogicDifficultyRule(18) & MinPartyRule  (3), # Neslug
    81: LogicDifficultyRule(18) & MinPartyRule  (3), # Ultima Buster
    82: LogicDifficultyRule(18) & MinSwimmerRule(3), # Shinryu
    83: LogicDifficultyRule(18) & MinPartyRule  (3), # Nemesis
}

superBossRuleDict: dict[int, Rule] = {
    44: LogicDifficultyRule(18) & MinPartyRule(3),                             # Omega Weapon
     2: LogicDifficultyRule(18) & MinPartyRule(3) & Has("Party Member: Yuna"), # Dark Valefor
    19: LogicDifficultyRule(18) & MinPartyRule(3),                             # Dark Ifrit
    13: LogicDifficultyRule(18) & MinPartyRule(3) & Has("Party Member: Yuna"), # Dark Ixion
    18: LogicDifficultyRule(18) & MinPartyRule(3),                             # Dark Shiva
    38: LogicDifficultyRule(18) & MinPartyRule(3),                             # Dark Bahamut
    34: LogicDifficultyRule(18) & MinPartyRule(3),                             # Dark Anima
    31: LogicDifficultyRule(18) & MinPartyRule(3),                             # Dark Yojimbo
    45: LogicDifficultyRule(18) & MinPartyRule(3),                             # Dark Mindy
    46: LogicDifficultyRule(18) & MinPartyRule(3),                             # Dark Sandy
    47: LogicDifficultyRule(18) & MinPartyRule(3),                             # Dark Cindy
  # 25: LogicDifficultyRule(18) & MinPartyRule(3),                             # Penance
}


# ---------------------------------------------------------------------------- #
#                                   Set Rules                                  #
# ---------------------------------------------------------------------------- #

def set_rules(world: FFXWorld) -> None:
    # ------------------------------------------------------------------------ #
    #                          Aeon Related Locations                          #
    # ------------------------------------------------------------------------ #
    
    # -------------------------------- Remiem -------------------------------- #
    # Valefor fight
    world.set_rule(world.get_location(world.location_id_to_name[379 | TreasureOffset]), MinSummonRule(2) | (MinSummonRule(1) & NotRule(Has(f"Party Member: Valefor"))))
    # Ifrit fight
    world.set_rule(world.get_location(world.location_id_to_name[381 | TreasureOffset]), MinSummonRule(2) | (MinSummonRule(1) & NotRule(Has(f"Party Member: Ifrit"))))
    # Ixion fight
    world.set_rule(world.get_location(world.location_id_to_name[383 | TreasureOffset]), MinSummonRule(2) | (MinSummonRule(1) & NotRule(Has(f"Party Member: Ixion"))))
    # Shiva fight
    world.set_rule(world.get_location(world.location_id_to_name[385 | TreasureOffset]), MinSummonRule(2) | (MinSummonRule(1) & NotRule(Has(f"Party Member: Shiva"))))
    # Bahamut fight
    world.set_rule(world.get_location(world.location_id_to_name[334 | TreasureOffset]), MinSummonRule(2) | (MinSummonRule(1) & NotRule(Has(f"Party Member: Bahamut"))))
    # Yojimbo fight
    world.set_rule(world.get_location(world.location_id_to_name[388 | TreasureOffset]), MinSummonRule(2) & Has(f"Party Member: Yojimbo"))
    # Anima fight
    world.set_rule(world.get_location(world.location_id_to_name[390 | TreasureOffset]), MinSummonRule(2) & HasAll(*[f"Party Member: {name}" for name in ["Yojimbo", "Anima"]]))
    # Magus Sisters fight
    world.set_rule(world.get_location(world.location_id_to_name[392 | TreasureOffset]), MinSummonRule(2) & HasAll(*[f"Party Member: {name}" for name in ["Yojimbo", "Anima", "Magus Sisters"]]))
    # Send Belgemine? (Moon sigil)
    world.set_rule(world.get_location(world.location_id_to_name[275 | TreasureOffset]), MinSummonRule(2) & HasAll(*[f"Party Member: {name}" for name in ["Yojimbo", "Anima", "Magus Sisters"]]))

    # ------------------------------- Belgemine ------------------------------ #
    # Mi'ihen fight
    world.set_rule(world.get_location(world.location_id_to_name[186 | TreasureOffset]), MinSummonRule(2) | (MinSummonRule(1) & NotRule(Has(f"Party Member: Ifrit"))))
    # Moonflow fight
    world.set_rule(world.get_location(world.location_id_to_name[372 | TreasureOffset]), MinSummonRule(2) | (MinSummonRule(1) & NotRule(Has(f"Party Member: Ixion"))))
    # Calm Lands fight
    world.set_rule(world.get_location(world.location_id_to_name[187 | TreasureOffset]), MinSummonRule(2) | (MinSummonRule(1) & NotRule(Has(f"Party Member: Shiva"))))

    # --------------------------------- Aeons -------------------------------- #
    # Anima
    world.set_rule(world.get_location(world.location_id_to_name[13 | PartyMemberOffset]), 
                   CanReachLocation(world.location_id_to_name[ 15 | TreasureOffset]) &  # Besaid
                   CanReachLocation(world.location_id_to_name[ 19 | TreasureOffset]) &  # Kilika
                   CanReachLocation(world.location_id_to_name[484 | TreasureOffset]) &  # Djose
                   CanReachLocation(world.location_id_to_name[485 | TreasureOffset]) &  # Macalania
                   CanReachLocation(world.location_id_to_name[217 | TreasureOffset]) &  # Bevelle
                   CanReachLocation(world.location_id_to_name[209 | TreasureOffset])    # Zanarkand
                   )
    # Magus Sisters
    world.set_rule(world.get_location(world.location_id_to_name[15 | PartyMemberOffset]), HasAll(*["Flower Scepter", "Blossom Crown"]))


    # ------------------------------------------------------------------------ #
    #                                 Captures                                 #
    # ------------------------------------------------------------------------ #

    # ---------------------------- Fiend Captures ---------------------------- #
    # If AlwaysCapture, Arena region not required for Fiend Capture checks, only rewards & bosses
    if not world.options.always_capture.value:
        for location_id in range(104):
            if (not location_id == 43 and not location_id == 59):
                location = world.get_location(world.location_id_to_name[location_id | CaptureOffset])
                world.set_rule(location, CanReachRegion("Monster Arena"))

    # ----------------------------- Area Conquest ---------------------------- #
    area_conquest = [
        (424, 49, (8, 15, 27,                                     )),  # Stratoavis
        (425, 50, (21, 30, 38, 61,                                )),  # Malboro Menace
        (426, 51, (0, 9, 22, 34, 47, 50, 62, 85,                  )),  # Kottos
        (427, 52, (5, 16, 23, 40, 51, 63, 91,                     )),  # Coeurlregina
        (428, 53, (1, 10, 17, 28, 31, 79, 83                      )),  # Jormungand
        (429, 54, (6, 24, 35, 52, 64, 76, 87, 89,                 )),  # Cactuar King
        (430, 55, (2, 3, 11, 18, 25, 32, 36, 65, 71, 94,          )),  # Espada
        (431, 56, (12, 29, 41, 42, 53, 88,                        )),  # Abyss Worm
        (432, 57, (4, 13, 19, 33, 55, 57, 72, 73, 80,             )),  # Chimerageist
        (433, 58, (7, 26, 44, 48, 54, 66, 68, 92, 98,             )),  # Don Tonberry
        (434, 59, (14, 20, 37, 39, 45, 46, 49, 58, 60, 69, 84, 86,)),  # Catoblepas
        (435, 60, (56, 70, 75, 77, 78, 81, 90, 93, 97,            )),  # Abaddon
        (436, 61, (67, 74, 82, 95, 96, 99, 100, 101, 102, 103,    )),  # Vorban
    ]
    for location_id, boss_id, fiend_ids in area_conquest:
        location = world.get_location(world.location_id_to_name[location_id | TreasureOffset])
        boss = world.get_location(world.location_id_to_name[boss_id | BossOffset])
        
        fiend_rule: Rule = None
        for fiend_id in fiend_ids:
            fiend = world.get_location(world.location_id_to_name[fiend_id | CaptureOffset])
            if fiend_rule is not None:
                fiend_rule &= CanReachLocation(fiend.name)
            else:
                fiend_rule = CanReachLocation(fiend.name)
        
        world.set_rule(location, fiend_rule)
        world.set_rule(boss, CanReachLocation(location.name) & arenaBossRuleDict[boss_id])

    # --------------------------- Species Conquest --------------------------- #
    species_conquest = [
        (437, 62, (8, 9, 10, 11, 12, 13, 14,   )), # Fenrir
        (438, 63, (21, 22, 23, 24, 25, 26, 100,)), # Ornitholestes
        (439, 64, (27, 28, 29,                 )), # Pteryx
        (440, 65, (30, 31, 32, 33,             )), # Hornet
        (441, 66, (5, 6, 7,                    )), # Vidatu
        (442, 67, (34, 35, 36, 37, 102,        )), # One-Eye
        (443, 68, (15, 16, 17, 18, 19, 20,     )), # Jumbo Flan
        (444, 69, (61, 62, 63, 64, 65, 66, 67, )), # Nega Elemental
        (445, 70, (0, 1, 2, 3, 4, 101,         )), # Tanket
        (446, 71, (50, 51, 52, 53, 54,         )), # Fafnir
        (447, 72, (91, 92, 93,                 )), # Sleep Sprout
        (448, 73, (85, 86, 95,                 )), # Bomb King
        (449, 74, (47, 48, 49,                 )), # Juggernaut
        (450, 75, (76, 77, 78,                 )), # Ironclad
    ]
    for location_id, boss_id, fiend_ids in species_conquest:
        location = world.get_location(world.location_id_to_name[location_id | TreasureOffset])
        boss = world.get_location(world.location_id_to_name[boss_id | BossOffset])
        
        fiend_rule: Rule = None
        for fiend_id in fiend_ids:
            fiend = world.get_location(world.location_id_to_name[fiend_id | CaptureOffset])
            if fiend_rule is not None:
                fiend_rule &= CanReachLocation(fiend.name)
            else:
                fiend_rule = CanReachLocation(fiend.name)
        
        world.set_rule(location, fiend_rule)
        world.set_rule(boss, CanReachLocation(location.name) & arenaBossRuleDict[boss_id])

    # ------------------------------ Mars Sigil ------------------------------ #
    conquest_locations = [world.get_location(world.location_id_to_name[id | TreasureOffset]) for id in list(range(424, 451))]
    if world.options.creation_rewards.value == world.options.creation_rewards.option_area:
        for location in [world.get_location(world.location_id_to_name[id | TreasureOffset]) for id in list(range(437, 451))]:
            conquest_locations.remove(location)
    location = world.get_location(world.location_id_to_name[276 | TreasureOffset])
    world.set_rule(location, CanReachMinimumLocationRule(conquest_locations, 10))

    # -------------------- Original Creations - Conquests -------------------- #
    original_creation_conquests = [
        (451, 76, area_conquest,    2), # Earth Eather
        (452, 77, species_conquest, 2), # Greater Sphere
        (453, 78, area_conquest,    6), # Catastrophe
        (454, 79, species_conquest, 6), # Th'uban
    ]
    for location_id, boss_id, arena_type, creations_required in original_creation_conquests:
        location = world.get_location(world.location_id_to_name[location_id | TreasureOffset])
        boss = world.get_location(world.location_id_to_name[boss_id | BossOffset])
        capture_locations = [world.get_location(world.location_id_to_name[arena_id | TreasureOffset]) for arena_id, _, _ in arena_type]
        
        world.set_rule(location, CanReachMinimumLocationRule(capture_locations, creations_required))
        world.set_rule(boss, CanReachLocation(location.name) & arenaBossRuleDict[boss_id])
    
    # --------------------- Original Creations - Captures -------------------- #
    original_creation_captures = [
        (455, 80), # Neslug (1x Capture)
        (456, 81), # Ultima Buster (5x Captures)
        (458, 83), # Nemesis (10x Captures)
    ]
    capture_regions = [
        "Besaid Island 1st visit",
        "Kilika 1st visit: Pre-Geneaux",
        "Mi'ihen Highroad 1st visit: Post-Chocobo Eater",
        "Mushroom Rock Road 1st visit: Pre-Sinspawn Gui",
        "Djose 1st visit",
        "Moonflow 1st visit: Pre-Extractor",
        "Thunder Plains 1st visit",
        "Lake Macalania 1st visit: Pre-Crawler",
        "Bikanel 1st visit: Post-Zu",
        "Calm Lands 1st visit: Pre-Defender X",
        "Cavern of the Stolen Fayth 1st visit",
        "Mt. Gagazet 1st visit: Post-Seymour Flux",
        "Sin: Post-Seymour Omnis",
        "Omega Ruins: Pre-Ultima Weapon"
    ]
    for location_id, boss_id in original_creation_captures:
        location = world.get_location(world.location_id_to_name[location_id | TreasureOffset])
        boss = world.get_location(world.location_id_to_name[boss_id | BossOffset])
        capture_region_rule: Rule = None
        for region in capture_regions:
            if capture_region_rule is not None:
                capture_region_rule &= CanReachRegion(region)
            else:
                capture_region_rule = CanReachRegion(region)

        world.set_rule(location, capture_region_rule)
        world.set_rule(boss, CanReachLocation(location.name) & arenaBossRuleDict[boss_id])

    # --------------- Shinryu (Underwater Captures in Gagazet) --------------- #
    location = world.get_location(world.location_id_to_name[457 | TreasureOffset])
    boss = world.get_location(world.location_id_to_name[82 | BossOffset])
    
    world.set_rule(location, CanReachRegion("Mt. Gagazet 1st visit: Post-Seymour Flux"))
    world.set_rule(boss, CanReachLocation(location.name) & arenaBossRuleDict[82])

    # ------------- Nemesis requires killing all other creations ------------- #
    nemesis = world.get_location(world.location_id_to_name[83 | BossOffset])
    creation_bosses_rule: Rule = None
    for _, rule in arenaBossRuleDict.items():
        if creation_bosses_rule is not None:
            creation_bosses_rule &= rule
        else:
            creation_bosses_rule = rule
    world.set_rule(nemesis, creation_bosses_rule)
    world.set_rule(world.get_location(world.location_id_to_name[496 | TreasureOffset]), CanReachLocation(nemesis.name))


    # ------------------------------------------------------------------------ #
    #                               Super Bosses                               #
    # ------------------------------------------------------------------------ #
    for boss_id, rule in superBossRuleDict.items():
        boss: Location = world.get_location(world.location_id_to_name[boss_id | BossOffset])
        world.set_rule(boss, rule)

    
    # ------------------------------------------------------------------------ #
    #                                Celestials                                #
    # ------------------------------------------------------------------------ #
    
    # --------------------------- Celestial Weapons -------------------------- #
    celestial_weapon_locations = [
        5,
        93,
        #99, # Requires Rusty Sword
        113,
        114,
        188,
        #214, # Airship password location
    ]
    for location_id in celestial_weapon_locations:
        location = world.get_location(world.location_id_to_name[location_id | TreasureOffset])
        world.set_rule(location, Has("Progressive Mirror", count=2))

    # Masamune
    world.set_rule(world.get_location(world.location_id_to_name[99 | TreasureOffset]), Has("Progressive Mirror", count=2) & Has("Rusty Sword"))

    # Celestial Mirror
    world.set_rule(world.get_location(world.location_id_to_name[111 | TreasureOffset]), Has("Progressive Mirror", count=1))

    # Mercury Sigil
    world.set_rule(world.get_location(world.location_id_to_name[279 | TreasureOffset]), CanReachRegion("Airship 1st visit: Post-Evrae"))

    # -------------------------- Celestial Upgrades -------------------------- #
    celestial_upgrades = [
        (38, 0x25, "Sun"),
        (40, 0x24, "Moon"),
        (42, 0x1e, "Mars"),
        (44, 0x38, "Saturn"),
        (46, 0x1a, "Jupiter"),
        (48, 0x03, "Venus"),
        (50, 0x3d, "Mercury"),
    ]
    for crest_id, weapon_id, celestial in celestial_upgrades:
        world.set_rule(world.get_location(world.location_id_to_name[crest_id | OtherOffset]),
                       Has("Progressive Mirror", count=2) & HasAll(*[world.item_id_to_name[weapon_id | equipItemOffset], f"{celestial} Crest"]))
        world.set_rule(world.get_location(world.location_id_to_name[crest_id+1 | OtherOffset]),
                       Has("Progressive Mirror", count=2) & HasAll(*[world.item_id_to_name[weapon_id | equipItemOffset], f"{celestial} Crest", f"{celestial} Sigil"]))


    # ------------------------------------------------------------------------ #
    #                                  Primers                                 #
    # ------------------------------------------------------------------------ #
    # Complete Al Bhed Primers
    world.set_rule(world.get_location(world.location_id_to_name[405 | TreasureOffset]), Has("Progressive Al Bhed Primer", count=26))


    # ---------------------------------------------------------------------------- #
    #                                  Overdrives                                  #
    # ---------------------------------------------------------------------------- #

    # ----------------------------------- Tidus ---------------------------------- #
    combat_regions: list[str] = [
        "Besaid Island 1st visit",
        "Kilika 1st visit: Pre-Geneaux",
        "Mi'ihen Highroad 1st visit: Pre-Chocobo Eater",
        "Mushroom Rock Road 1st visit: Pre-Sinspawn Gui",
        "Djose 1st visit",
        "Moonflow 1st visit: Pre-Extractor",
        "Thunder Plains 1st visit",
        "Macalania Woods 1st visit: Pre-Spherimorph",
        "Bikanel 1st visit: Post-Zu",
        "Airship 1st visit: Pre-Evrae",
        "Bevelle 1st visit: Pre-Isaaru",
        "Calm Lands 1st visit: Pre-Defender X",
        "Cavern of the Stolen Fayth 1st visit",
        "Mt. Gagazet 1st visit: Post-Biran and Yenke",
        "Zanarkand Ruins 1st visit: Pre-Spectral Keeper",
        "Sin: Pre-Seymour Omnis",
        "Omega Ruins: Pre-Ultima Weapon"
    ]
    overdrive_regions = [world.get_region(region_name) for region_name in combat_regions]
    
    slice_and_dice  = world.get_location(world.location_id_to_name[1 | OverdriveOffset])
    energy_rain     = world.get_location(world.location_id_to_name[2 | OverdriveOffset])
    blitz_ace       = world.get_location(world.location_id_to_name[3 | OverdriveOffset])

    world.set_rule(slice_and_dice, CanReachMinimumRegionRule(overdrive_regions, 2))
    world.set_rule(energy_rain,    CanReachMinimumRegionRule(overdrive_regions, 4))
    world.set_rule(blitz_ace,      CanReachMinimumRegionRule(overdrive_regions, 8))

    # ----------------------------------- Auron ---------------------------------- #
    shooting_star   = world.get_location(world.location_id_to_name[4 | OverdriveOffset])
    banishing_blade = world.get_location(world.location_id_to_name[6 | OverdriveOffset])
    tornado         = world.get_location(world.location_id_to_name[7 | OverdriveOffset])

    world.set_rule(shooting_star,   Has("Progressive Jecht's Sphere", count=1))
    world.set_rule(banishing_blade, Has("Progressive Jecht's Sphere", count=3))
    world.set_rule(tornado,         Has("Progressive Jecht's Sphere", count=10))

    # ----------------------------------- Wakka ---------------------------------- #
    status_reels    = world.get_location(world.location_id_to_name[22 | OverdriveOffset])
    aurochs_reels   = world.get_location(world.location_id_to_name[23 | OverdriveOffset])

    world.set_rule(status_reels,  Has("Overdrive: Attack Reels"))
    world.set_rule(aurochs_reels, Has("Overdrive: Status Reels"))

    # ---------------------------------------------------------------------------- #
    #                                     Todo                                     #
    # ---------------------------------------------------------------------------- #

    # TODO: Disabled for now due to multiple bugs related to this location (Ship softlocks + possible Macalania softlock)
    # Clasko S.S. Liki second visit (Talk to Clasko before Crawler and make sure to have him become a Chocobo Breeder)
    #add_rule(world.get_location(world.location_id_to_name[336 | TreasureOffset]),
    #         lambda state: state.can_reach_region("Lake Macalania 1st visit: Pre-Crawler", world.player))
