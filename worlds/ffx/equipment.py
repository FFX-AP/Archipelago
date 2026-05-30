from typing import NamedTuple, TYPE_CHECKING
from enum import IntEnum

from BaseClasses import ItemClassification

if TYPE_CHECKING:
    from worlds.ffx import FFXWorld
else:
    FFXWorld = object

class GearAbility(NamedTuple):
    name: str
    id: int
    group: int
    group_level: int
    international_bonus: int | None

class GearFlag(IntEnum):
    NONE        = 0
    HIDDEN      = 2
    CELESTIAL   = 4
    BROTHERHOOD = 8

class GearType(IntEnum):
    WEAPON     = 0
    ARMOR      = 1

class GearDamageFormula(IntEnum):
    WEAPON     = 0
    ARMOR      = 1

class PlySaveId(IntEnum):
    TIDUS   = 0x00
    YUNA    = 0x01
    AURON   = 0x02
    KIMAHRI = 0x03
    WAKKA   = 0x04
    LULU    = 0x05
    RIKKU   = 0x06
    SEYMOUR = 0x07

class Gear(NamedTuple):
    flags: GearFlag
    owner: PlySaveId
    type: GearType
    dmg_formula: int
    power: int
    crit_bonus: int
    slot_count: int
    abilities: list[GearAbility]


class GearData(NamedTuple):
    name: str
    progression: ItemClassification
    flags: GearFlag
    owner: PlySaveId
    type: GearType
    slots: int
    abilities: list[GearAbility | None]
    itemID: int = 0x00

ownerToCelestialFormula: dict[PlySaveId, int] = {
    PlySaveId.TIDUS:   0x11,
    PlySaveId.YUNA:    0x12,
    PlySaveId.AURON:   0x13,
    PlySaveId.KIMAHRI: 0x11,
    PlySaveId.WAKKA:   0x11,
    PlySaveId.LULU:    0x12,
    PlySaveId.RIKKU:   0x11,
    PlySaveId.SEYMOUR: 0x12,
}

def generate_equipment(world: FFXWorld, owner: PlySaveId, flags: GearFlag, gear_type: GearType, guaranteed_slots: int, guaranteed_abilities: list[GearAbility | list[GearAbility]]) -> Gear:
    dmg_formula = 1
    power = 16
    crit_bonus = 3

    if flags == GearFlag.CELESTIAL:
        dmg_formula = ownerToCelestialFormula[owner]
        slots = 4
        abilities = [id_to_ability[0x14], None, None, None] # No AP [8014h], Empty, Empty, Empty
    elif flags == GearFlag.BROTHERHOOD:
        slots = 4
        abilities = [id_to_ability[0x63], id_to_ability[0x64], id_to_ability[0x2A], id_to_ability[0x00]] # Strength +5% [8063h], Strength +10% [8064h], Waterstrike [802Ah], Sensor [8000h]
    else:
        slots = world.random.randint(guaranteed_slots, 4)
        num_abilities = world.random.randint(min(guaranteed_slots, len(guaranteed_abilities)), slots)


        has_ribbon = False
        abilities: list[GearAbility | None] = [None]*slots

        if guaranteed_slots < len(guaranteed_abilities):
            ability_list = world.random.sample(guaranteed_abilities, guaranteed_slots)
        else:
            ability_list = guaranteed_abilities

        for i, ability in enumerate(ability_list):
            if ability is None:
                num_abilities -= 1
                continue
            if isinstance(ability, list):
                ability = world.random.choice([x for x in ability if x not in abilities])
            abilities[i] = ability
            if ability.international_bonus == 0xFF:
                has_ribbon = True

        for i in range(num_abilities):
            while abilities[i] is None:
                ability = world.random.choice(gear_abilities)
                possible = True
                for other_ability in abilities[:i]:
                    if ability.group == other_ability.group and ability.group_level <= other_ability.group_level:
                        possible = False
                    if has_ribbon and ability.international_bonus == 0xFE:
                        possible = False

                if possible:
                    abilities[i] = ability
                    if ability.international_bonus == 0xFF:
                        has_ribbon = True


    return Gear(flags, owner, gear_type, dmg_formula, power, crit_bonus, slots, abilities)

def get_gear_item(gear: Gear) -> GearData | None:
    for g in gear_name_data:
        if g.owner != gear.owner or g.type != gear.type:
            continue

        if gear.flags != GearFlag.NONE and g.flags == gear.flags:
            return g

        # Default name
        if g.slots == 0 and len(g.abilities) == 0:
            return g

        # x slots condition
        if len(g.abilities) == 0 and g.slots == gear.slot_count:
            return g

        matches = []
        used = []
        for i, x in enumerate(g.abilities):
            match = False
            for j, y in enumerate(gear.abilities):
                if j in used:
                    continue
                if y is not None:
                    if isinstance(x, list):
                        match = any([z.id == y.id for z in x])
                    else:
                        match = x.id == y.id
                if match:
                    used.append(j)
                    break
            matches.append(match)

        if len([x for x in matches if x]) >= g.slots:
            return g

    return None

def verify_gear_name(item: GearData, gear: Gear) -> bool:
    real_item = get_gear_item(gear)
    if real_item is None or real_item.name != item.name:
        return False
    return True

def generate_and_verify(world: FFXWorld, item: GearData) -> Gear:
    success = False
    while not success:
        gear = generate_equipment(world, item.owner, item.flags, item.type, item.slots, item.abilities)
        success = verify_gear_name(item, gear)
    return gear

gear_abilities: list[GearAbility] = [
    GearAbility("Sensor",             0x00,   1, 0, None),
    GearAbility("First Strike",       0x01,   2, 0, None),
    GearAbility("Initiative",         0x02,   3, 0, None),
    GearAbility("Counterattack",      0x03,   4, 1, None),
    GearAbility("Evade & Counter",    0x04,   4, 2, None),
    GearAbility("Magic Counter",      0x05,   6, 0, None),
    GearAbility("Magic Booster",      0x06,   7, 0, None),
    GearAbility("Alchemy",            0x07,  10, 0, None),
    GearAbility("Auto-Potion",        0x08,  11, 0, None),
    GearAbility("Auto-Med",           0x09,  12, 0, None),
    GearAbility("Auto-Phoenix",       0x0A,  13, 0, None),
    GearAbility("Piercing",           0x0B,  14, 0, None),
    GearAbility("Half MP Cost",       0x0C,  15, 1, None),
    GearAbility("One MP Cost",        0x0D,  15, 2, None),
    GearAbility("Double Overdrive",   0x0E,  16, 2, None),
    GearAbility("Triple Overdrive",   0x0F,  16, 3, None),
    GearAbility("SOS Overdrive",      0x10,  16, 1, None),
    GearAbility("Overdrive → AP",     0x11,  20, 0, None),
    GearAbility("Double AP",          0x12,  21, 2, None),
    GearAbility("Triple AP",          0x13,  21, 3, None),
    GearAbility("No AP",              0x14,  21, 1, None),
    GearAbility("Pickpocket",         0x15,  24, 1, None),
    GearAbility("Master Thief",       0x16,  24, 2, None),
    GearAbility("Break HP Limit",     0x17,  26, 0, None),
    GearAbility("Break MP Limit",     0x18,  27, 0, None),
    GearAbility("Break Damage Limit", 0x19,  28, 0, None),
    GearAbility("Gillionaire",        0x1A,  31, 0, None),
    GearAbility("HP Stroll",          0x1B,  32, 0, None),
    GearAbility("MP Stroll",          0x1C,  33, 0, None),
    GearAbility("No Encounters",      0x1D,  34, 0, None),
    GearAbility("Firestrike",         0x1E,  35, 0, None),
    GearAbility("Fire Ward",          0x1F,  36, 2, None),
    GearAbility("Fireproof",          0x20,  36, 3, None),
    GearAbility("Fire Eater",         0x21,  36, 4, None),
    GearAbility("Icestrike",          0x22,  39, 0, None),
    GearAbility("Ice Ward",           0x23,  40, 2, None),
    GearAbility("Iceproof",           0x24,  40, 3, None),
    GearAbility("Ice Eater",          0x25,  40, 4, None),
    GearAbility("Lightningstrike",    0x26,  43, 0, None),
    GearAbility("Lightning Ward",     0x27,  44, 2, None),
    GearAbility("Lightningproof",     0x28,  44, 3, None),
    GearAbility("Lightning Eater",    0x29,  44, 4, None),
    GearAbility("Waterstrike",        0x2A,  47, 0, None),
    GearAbility("Water Ward",         0x2B,  48, 2, None),
    GearAbility("Waterproof",         0x2C,  48, 3, None),
    GearAbility("Water Eater",        0x2D,  48, 4, None),
    GearAbility("Deathstrike",        0x2E,  51, 2, None),
    GearAbility("Deathtouch",         0x2F,  51, 1, None),
    GearAbility("Deathproof",         0x30,  53, 2, None),
    GearAbility("Death Ward",         0x31,  53, 1, None),
    GearAbility("Zombiestrike",       0x32,  55, 2, None),
    GearAbility("Zombietouch",        0x33,  55, 1, None),
    GearAbility("Zombieproof",        0x34,  57, 2,  254),
    GearAbility("Zombie Ward",        0x35,  57, 1,  254),
    GearAbility("Stonestrike",        0x36,  59, 2, None),
    GearAbility("Stonetouch",         0x37,  59, 1, None),
    GearAbility("Stoneproof",         0x38,  61, 2,  254),
    GearAbility("Stone Ward",         0x39,  61, 1,  254),
    GearAbility("Poisonstrike",       0x3A,  63, 2, None),
    GearAbility("Poisontouch",        0x3B,  63, 1, None),
    GearAbility("Poisonproof",        0x3C,  65, 2,  254),
    GearAbility("Poison Ward",        0x3D,  65, 1,  254),
    GearAbility("Sleepstrike",        0x3E,  67, 2, None),
    GearAbility("Sleeptouch",         0x3F,  67, 1, None),
    GearAbility("Sleepproof",         0x40,  69, 2,  254),
    GearAbility("Sleep Ward",         0x41,  69, 1,  254),
    GearAbility("Silencestrike",      0x42,  71, 2, None),
    GearAbility("Silencetouch",       0x43,  71, 1, None),
    GearAbility("Silenceproof",       0x44,  73, 2,  254),
    GearAbility("Silence Ward",       0x45,  73, 1,  254),
    GearAbility("Darkstrike",         0x46,  75, 2, None),
    GearAbility("Darktouch",          0x47,  75, 1, None),
    GearAbility("Darkproof",          0x48,  77, 2,  254),
    GearAbility("Dark Ward",          0x49,  77, 1,  254),
    GearAbility("Slowstrike",         0x4A,  79, 2, None),
    GearAbility("Slowtouch",          0x4B,  79, 1, None),
    GearAbility("Slowproof",          0x4C,  81, 2,  254),
    GearAbility("Slow Ward",          0x4D,  81, 1,  254),
    GearAbility("Confuseproof",       0x4E,  83, 2,  254),
    GearAbility("Confuse Ward",       0x4F,  83, 1,  254),
    GearAbility("Berserkproof",       0x50,  85, 2,  254),
    GearAbility("Berserk Ward",       0x51,  85, 1,  254),
    GearAbility("Curseproof",         0x52,  87, 2, None),
    #GearAbility("Curse Ward",         0x53,  87, 1, None),
    GearAbility("Auto-Shell",         0x54,  89, 2, None),
    GearAbility("Auto-Protect",       0x55,  90, 2, None),
    GearAbility("Auto-Haste",         0x56,  91, 2, None),
    GearAbility("Auto-Regen",         0x57,  92, 2, None),
    GearAbility("Auto-Reflect",       0x58,  93, 2, None),
    GearAbility("SOS Shell",          0x59,  89, 1, None),
    GearAbility("SOS Protect",        0x5A,  90, 1, None),
    GearAbility("SOS Haste",          0x5B,  91, 1, None),
    GearAbility("SOS Regen",          0x5C,  92, 1, None),
    GearAbility("SOS Reflect",        0x5D,  93, 1, None),
    GearAbility("SOS NulTide",        0x5E,  48, 1, None),
    GearAbility("SOS NulFrost",       0x5F,  40, 1, None),
    GearAbility("SOS NulShock",       0x60,  44, 1, None),
    GearAbility("SOS NulBlaze",       0x61,  36, 1, None),
    GearAbility("Strength +3%",       0x62, 103, 0, None),
    GearAbility("Strength +5%",       0x63, 104, 0, None),
    GearAbility("Strength +10%",      0x64, 105, 0, None),
    GearAbility("Strength +20%",      0x65, 106, 0, None),
    GearAbility("Magic +3%",          0x66, 107, 0, None),
    GearAbility("Magic +5%",          0x67, 108, 0, None),
    GearAbility("Magic +10%",         0x68, 109, 0, None),
    GearAbility("Magic +20%",         0x69, 110, 0, None),
    GearAbility("Defense +3%",        0x6A, 111, 0, None),
    GearAbility("Defense +5%",        0x6B, 112, 0, None),
    GearAbility("Defense +10%",       0x6C, 113, 0, None),
    GearAbility("Defense +20%",       0x6D, 114, 0, None),
    GearAbility("Magic Def +3%",      0x6E, 115, 0, None),
    GearAbility("Magic Def +5%",      0x6F, 116, 0, None),
    GearAbility("Magic Def +10%",     0x70, 117, 0, None),
    GearAbility("Magic Def +20%",     0x71, 118, 0, None),
    GearAbility("HP +5%",             0x72, 119, 0, None),
    GearAbility("HP +10%",            0x73, 120, 0, None),
    GearAbility("HP +20%",            0x74, 121, 0, None),
    GearAbility("HP +30%",            0x75, 122, 0, None),
    GearAbility("MP +5%",             0x76, 123, 0, None),
    GearAbility("MP +10%",            0x77, 124, 0, None),
    GearAbility("MP +20%",            0x78, 125, 0, None),
    GearAbility("MP +30%",            0x79, 126, 0, None),
    GearAbility("Capture",            0x7A, 127, 0, None),
    GearAbility("",                   0x7B, 128, 0, None),
    #GearAbility("Distill Power",      0x7C, 129, 1,    1),
    #GearAbility("Distill Mana",       0x7D, 129, 1,    2),
    #GearAbility("Distill Speed",      0x7E, 129, 1,    3),
    #GearAbility("Distill Ability",    0x7F, 129, 1,    4),
    GearAbility("Ribbon",             0x80, 130, 0,  255),
    #GearAbility("Extra 1",            0x81,   0, 0, None),
    #GearAbility("Extra 2",            0x82,   0, 0, None),
    #GearAbility("Extra 3",            0x83,   0, 0, None),
    #GearAbility("Extra 4",            0x84,   0, 0, None),
    #GearAbility("Extra 5",            0x85,   0, 0, None),
]

id_to_ability: dict[int, GearAbility] = {a.id: a for a in gear_abilities}

strength_abilities: list[GearAbility] = [id_to_ability[x] for x in [0x62, 0x63, 0x64, 0x65]]
magic_abilities:    list[GearAbility] = [id_to_ability[x] for x in [0x66, 0x67, 0x68, 0x69]]
elemental_strikes:  list[GearAbility] = [id_to_ability[x] for x in [0x1E, 0x22, 0x26, 0x2A]]
status_strikes:     list[GearAbility] = [id_to_ability[x] for x in [0x2E, 0x32, 0x36, 0x3A, 0x3E, 0x42, 0x46, 0x4A]]
status_touches:     list[GearAbility] = [id_to_ability[x] for x in [0x2F, 0x33, 0x37, 0x3B, 0x3F, 0x43, 0x47, 0x4B]]

elemental_eaters:        list[GearAbility] = [id_to_ability[x] for x in [0x21, 0x25, 0x29, 0x2D]]
elemental_proofs:        list[GearAbility] = [id_to_ability[x] for x in [0x20, 0x24, 0x28, 0x2C]]
status_proofs:           list[GearAbility] = [id_to_ability[x] for x in [0x30, 0x34, 0x38, 0x3C, 0x40, 0x44, 0x48, 0x4C, 0x4E, 0x50, 0x52]]
defense_abilities:       list[GearAbility] = [id_to_ability[x] for x in [0x6A, 0x6B, 0x6C, 0x6D]]
magic_defense_abilities: list[GearAbility] = [id_to_ability[x] for x in [0x6E, 0x6F, 0x70, 0x71]]
hp_abilities:            list[GearAbility] = [id_to_ability[x] for x in [0x72, 0x73, 0x74, 0x75]]
mp_abilities:            list[GearAbility] = [id_to_ability[x] for x in [0x76, 0x77, 0x78, 0x79]]
auto_abilities:          list[GearAbility] = [id_to_ability[x] for x in [0x08, 0x09, 0x0A, 0x54, 0x55, 0x56, 0x57, 0x58]]
sos_abilities:           list[GearAbility] = [id_to_ability[x] for x in [0x10, 0x59, 0x5A, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F, 0x60, 0x61]]


gear_name_data: list[GearData] = [GearData(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7]) for x in [
    # Celestial
    ("Progressive Caladbolg",        ItemClassification.progression, GearFlag.CELESTIAL  , PlySaveId.TIDUS  , GearType.WEAPON, 4, [id_to_ability[0x14]], 0x0000),
    ("Progressive Nirvana",          ItemClassification.progression, GearFlag.CELESTIAL  , PlySaveId.YUNA   , GearType.WEAPON, 4, [id_to_ability[0x14]], 0x0001),
    ("Progressive Masamune",         ItemClassification.progression, GearFlag.CELESTIAL  , PlySaveId.AURON  , GearType.WEAPON, 4, [id_to_ability[0x14]], 0x0002),
    ("Progressive Spirit Lance",     ItemClassification.progression, GearFlag.CELESTIAL  , PlySaveId.KIMAHRI, GearType.WEAPON, 4, [id_to_ability[0x14]], 0x0003),
    ("Progressive World Champion",   ItemClassification.progression, GearFlag.CELESTIAL  , PlySaveId.WAKKA  , GearType.WEAPON, 4, [id_to_ability[0x14]], 0x0004),
    ("Progressive Onion Knight",     ItemClassification.progression, GearFlag.CELESTIAL  , PlySaveId.LULU   , GearType.WEAPON, 4, [id_to_ability[0x14]], 0x0005),
    ("Progressive Godhand",          ItemClassification.progression, GearFlag.CELESTIAL  , PlySaveId.RIKKU  , GearType.WEAPON, 4, [id_to_ability[0x14]], 0x0006),
    ("Progressive Dimittis",         ItemClassification.progression, GearFlag.CELESTIAL  , PlySaveId.SEYMOUR, GearType.WEAPON, 4, [id_to_ability[0x14]], 0x0007),

    # Brotherhood
    ("Progressive Brotherhood",      ItemClassification.progression, GearFlag.BROTHERHOOD, PlySaveId.TIDUS  , GearType.WEAPON, 4, [id_to_ability[0x63], id_to_ability[0x64], id_to_ability[0x2A], id_to_ability[0x00]], 0x0008),

    # Capture
    ("Tidus: Taming Sword",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x7A]], 0x0009),
    ("Yuna: Herding Staff",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x7A]], 0x000A),
    ("Auron: Beastmaster",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x7A]], 0x000B),
    ("Kimahri: Taming Spear",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x7A]], 0x000C),
    ("Wakka: Catcher",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x7A]], 0x000D),
    ("Lulu: Trapper Mog",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x7A]], 0x000E),
    ("Rikku: Iron Grip",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x7A]], 0x000F),
    ("Seymour: Subduing Scepter",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x7A]], 0x0010),

    # 4 Elemental strikes
    ("Tidus: Crystal Sword",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 4, elemental_strikes, 0x0011),
    ("Yuna: Arc Arcana",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 4, elemental_strikes, 0x0012),
    ("Auron: Conqueror",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 4, elemental_strikes, 0x0013),
    ("Kimahri: Quadforce",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 4, elemental_strikes, 0x0014),
    ("Wakka: Four-on-One",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 4, elemental_strikes, 0x0015),
    ("Lulu: Moomba Quartet",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 4, elemental_strikes, 0x0016),
    ("Rikku: Deus Ex Machina",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 4, elemental_strikes, 0x0017),
    ("Seymour: Arcane Scepter",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 4, elemental_strikes, 0x0018),

    # Break Damage Limit
    ("Tidus: Excalibur",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x19]], 0x0019),
    ("Yuna: Abraxas",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x19]], 0x001A),
    ("Auron: Heaven’s Cloud",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x19]], 0x001B),
    ("Kimahri: Gungnir",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x19]], 0x001C),
    ("Wakka: Grand Slam",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x19]], 0x001D),
    ("Lulu: Soul of Mog",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x19]], 0x001E),
    ("Rikku: Kaiser Knuckles",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x19]], 0x001F),
    ("Seymour: Heaven Fall",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x19]], 0x0020),

    # Triple Overdrive, Triple AP, and Overdrive → AP
    ("Tidus: Ragnarok",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 3, [id_to_ability[0x0F], id_to_ability[0x13], id_to_ability[0x11]], 0x0021),
    ("Yuna: Heavenly Axis",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 3, [id_to_ability[0x0F], id_to_ability[0x13], id_to_ability[0x11]], 0x0022),
    ("Auron: Muramasa",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 3, [id_to_ability[0x0F], id_to_ability[0x13], id_to_ability[0x11]], 0x0023),
    ("Kimahri: Luin",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 3, [id_to_ability[0x0F], id_to_ability[0x13], id_to_ability[0x11]], 0x0024),
    ("Wakka: Blowout",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 3, [id_to_ability[0x0F], id_to_ability[0x13], id_to_ability[0x11]], 0x0025),
    ("Lulu: Space Soul",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 3, [id_to_ability[0x0F], id_to_ability[0x13], id_to_ability[0x11]], 0x0026),
    ("Rikku: Victorix",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 3, [id_to_ability[0x0F], id_to_ability[0x13], id_to_ability[0x11]], 0x0027),
    ("Seymour: Transcendence",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 3, [id_to_ability[0x0F], id_to_ability[0x13], id_to_ability[0x11]], 0x0028),

    # Triple Overdrive and Overdrive → AP
    ("Tidus: Balmung",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 2, [id_to_ability[0x0F], id_to_ability[0x11]], 0x0029),
    ("Yuna: Judgment",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 2, [id_to_ability[0x0F], id_to_ability[0x11]], 0x002A),
    ("Auron: Alkaid",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 2, [id_to_ability[0x0F], id_to_ability[0x11]], 0x002B),
    ("Kimahri: Gae Bolg",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 2, [id_to_ability[0x0F], id_to_ability[0x11]], 0x002C),
    ("Wakka: Rout",                  ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 2, [id_to_ability[0x0F], id_to_ability[0x11]], 0x002D),
    ("Lulu: Space Master",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 2, [id_to_ability[0x0F], id_to_ability[0x11]], 0x002E),
    ("Rikku: Unlimited",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 2, [id_to_ability[0x0F], id_to_ability[0x11]], 0x002F),
    ("Seymour: Retribution",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 2, [id_to_ability[0x0F], id_to_ability[0x11]], 0x0030),

    # Double Overdrive and Double AP
    ("Tidus: Save the Queen",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 2, [id_to_ability[0x0E], id_to_ability[0x12]], 0x0031),
    ("Yuna: Seraphim Rod",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 2, [id_to_ability[0x0E], id_to_ability[0x12]], 0x0032),
    ("Auron: Peacemaker",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 2, [id_to_ability[0x0E], id_to_ability[0x12]], 0x0033),
    ("Kimahri: Venus Gospel",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 2, [id_to_ability[0x0E], id_to_ability[0x12]], 0x0034),
    ("Wakka: Tie Breaker",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 2, [id_to_ability[0x0E], id_to_ability[0x12]], 0x0035),
    ("Lulu: Space King",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 2, [id_to_ability[0x0E], id_to_ability[0x12]], 0x0036),
    ("Rikku: Warmonger",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 2, [id_to_ability[0x0E], id_to_ability[0x12]], 0x0037),
    ("Seymour: Deliverance",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 2, [id_to_ability[0x0E], id_to_ability[0x12]], 0x0038),

    # Triple Overdrive
    ("Tidus: Heartbreaker",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x0F]], 0x0039),
    ("Yuna: Rod of Roses",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x0F]], 0x003A),
    ("Auron: Genji Blade",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x0F]], 0x003B),
    ("Kimahri: Highwind",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x0F]], 0x003C),
    ("Wakka: Winning Streak",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x0F]], 0x003D),
    ("Lulu: Space Force",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x0F]], 0x003E),
    ("Rikku: Overload",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x0F]], 0x003F),
    ("Seymour: Ferrier of Souls",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x0F]], 0x0040),

    # Double Overdrive
    ("Tidus: Lionheart",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x0E]], 0x0041),
    ("Yuna: Nimbus Rod",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x0E]], 0x0042),
    ("Auron: Dragonkiller",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x0E]], 0x0043),
    ("Kimahri: Berserker",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x0E]], 0x0044),
    ("Wakka: Scoring Spree",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x0E]], 0x0045),
    ("Lulu: Space Energy",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x0E]], 0x0046),
    ("Rikku: Override",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x0E]], 0x0047),
    ("Seymour: Veil Piercer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x0E]], 0x0048),

    # Triple AP
    ("Tidus: Durandal",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x13]], 0x0049),
    ("Yuna: Wonder Wing",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x13]], 0x004A),
    ("Auron: Painkiller",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x13]], 0x004B),
    ("Kimahri: Horn of the Ronso",   ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x13]], 0x004C),
    ("Wakka: Triple Score",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x13]], 0x004D),
    ("Lulu: Comet Cactuar",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x13]], 0x004E),
    ("Rikku: Golden Arm",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x13]], 0x004F),
    ("Seymour: Benediction",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x13]], 0x0050),

    # Double AP
    ("Tidus: Ascalon",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x12]], 0x0051),
    ("Yuna: Wing Wand",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x12]], 0x0052),
    ("Auron: Divider",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x12]], 0x0053),
    ("Kimahri: Chariot",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x12]], 0x0054),
    ("Wakka: Double Score",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x12]], 0x0055),
    ("Lulu: Star Cactuar",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x12]], 0x0056),
    ("Rikku: Golden Hand",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x12]], 0x0057),
    ("Seymour: Rite of the Guado",   ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x12]], 0x0058),

    # Overdrive → AP
    ("Tidus: Ambitious",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x11]], 0x0059),
    ("Yuna: Wonder Wand",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x11]], 0x005A),
    ("Auron: The Nameless",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x11]], 0x005B),
    ("Kimahri: Transmuter",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x11]], 0x005C),
    ("Wakka: Rookie Star",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x11]], 0x005D),
    ("Lulu: Lord Cactuar",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x11]], 0x005E),
    ("Rikku: Ironside",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x11]], 0x005F),
    ("Seymour: Sublimator",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x11]], 0x0060),

    # SOS Overdrive
    ("Tidus: Hrunting",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x10]], 0x0061),
    ("Yuna: Laevatein",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x10]], 0x0062),
    ("Auron: Ogrekiller",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x10]], 0x0063),
    ("Kimahri: Kain’s Lancer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x10]], 0x0064),
    ("Wakka: Buzzerbeater",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x10]], 0x0065),
    ("Lulu: Space Power",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x10]], 0x0066),
    ("Rikku: Battle Freak",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x10]], 0x0067),
    ("Seymour: Fettered Malice",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x10]], 0x0068),

    # One MP Cost
    ("Tidus: Astral Sword",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x0D]], 0x0069),
    ("Yuna: Astral Rod",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x0D]], 0x006A),
    ("Auron: Murasame",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x0D]], 0x006B),
    ("Kimahri: Astral Spear",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x0D]], 0x006C),
    ("Wakka: Overtime",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x0D]], 0x006D),
    ("Lulu: Magical Cactuar",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x0D]], 0x006E),
    ("Rikku: Infinity",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x0D]], 0x006F),
    ("Seymour: Astral Scepter",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x0D]], 0x0070),

    # 4 status strikes
    ("Tidus: Apocalypse",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 4, status_strikes, 0x0071),
    ("Yuna: Chaos Rod",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 4, status_strikes, 0x0072),
    ("Auron: Riot Blade",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 4, status_strikes, 0x0073),
    ("Kimahri: Chaos Lance",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 4, status_strikes, 0x0074),
    ("Wakka: Penalty Master",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 4, status_strikes, 0x0075),
    ("Lulu: Chaotic Cait Sith",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 4, status_strikes, 0x0076),
    ("Rikku: Tempest Claw",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 4, status_strikes, 0x0077),
    ("Seymour: Chaos Scepter",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 4, status_strikes, 0x0078),

    # 4 Strength +%s
    ("Tidus: Master Sword",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 4, strength_abilities, 0x0079),
    ("Yuna: Power Staff",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 4, strength_abilities, 0x007A),
    ("Auron: Master Ogre",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 4, strength_abilities, 0x007B),
    ("Kimahri: Giant Spear",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 4, strength_abilities, 0x007C),
    ("Wakka: Ace Striker",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 4, strength_abilities, 0x007D),
    ("Lulu: Space Warrior",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 4, strength_abilities, 0x007E),
    ("Rikku: Spartan",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 4, strength_abilities, 0x007F),
    ("Seymour: Master Scepter",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 4, strength_abilities, 0x0080),

    # 4 Magic +%s
    ("Tidus: Runemaster",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 4, magic_abilities, 0x0081),
    ("Yuna: Shining Staff",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 4, magic_abilities, 0x0082),
    ("Auron: Master Djinn",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 4, magic_abilities, 0x0083),
    ("Kimahri: Titan Lance",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 4, magic_abilities, 0x0084),
    ("Wakka: Ace Wizard",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 4, magic_abilities, 0x0085),
    ("Lulu: Space Mage",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 4, magic_abilities, 0x0086),
    ("Rikku: Brunhilde",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 4, magic_abilities, 0x0087),
    ("Seymour: Wizard's Scepter",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 4, magic_abilities, 0x0088),

    # 3 Magic +%s and Magic Booster
    ("Tidus: Warlock",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 4, [id_to_ability[0x06], magic_abilities, magic_abilities, magic_abilities], 0x0089),
    ("Yuna: Faerie Staff",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 4, [id_to_ability[0x06], magic_abilities, magic_abilities, magic_abilities], 0x008A),
    ("Auron: Matoya’s Blade",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 4, [id_to_ability[0x06], magic_abilities, magic_abilities, magic_abilities], 0x008B),
    ("Kimahri: Eldritch Lance",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 4, [id_to_ability[0x06], magic_abilities, magic_abilities, magic_abilities], 0x008C),
    ("Wakka: Over the Top",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 4, [id_to_ability[0x06], magic_abilities, magic_abilities, magic_abilities], 0x008D),
    ("Lulu: Mana Mog",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 4, [id_to_ability[0x06], magic_abilities, magic_abilities, magic_abilities], 0x008E),
    ("Rikku: Valkyrie",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 4, [id_to_ability[0x06], magic_abilities, magic_abilities, magic_abilities], 0x008F),
    ("Seymour: Mana Scepter",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 4, [id_to_ability[0x06], magic_abilities, magic_abilities, magic_abilities], 0x0090),

    # Half MP Cost
    ("Tidus: Arc Sword",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x0C]], 0x0091),
    ("Yuna: Magistral Rod",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x0C]], 0x0092),
    ("Auron: Inducer",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x0C]], 0x0093),
    ("Kimahri: Shamanic Spear",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x0C]], 0x0094),
    ("Wakka: Halftime",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x0C]], 0x0095),
    ("Lulu: Cactuar Wizard",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x0C]], 0x0096),
    ("Rikku: Magical Rave",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x0C]], 0x0097),
    ("Seymour: Magistral Scepter",   ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x0C]], 0x0098),

    # Gillionaire
    ("Tidus: Gilventure",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x1A]], 0x0099),
    ("Yuna: El Dorado",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x1A]], 0x009A),
    ("Auron: Gilmonger",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x1A]], 0x009B),
    ("Kimahri: Prospector",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x1A]], 0x009C),
    ("Wakka: Free Agent",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x1A]], 0x009D),
    ("Lulu: Space Bandit",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x1A]], 0x009E),
    ("Rikku: Stickyfingers",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x1A]], 0x009F),
    ("Seymour: Resplendence",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x1A]], 0x00A0),

    # 3 elemental strikes
    ("Tidus: Tri-Steel",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 3, elemental_strikes, 0x00A1),
    ("Yuna: Tri-Rod",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 3, elemental_strikes, 0x00A2),
    ("Auron: Ichimonji",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 3, elemental_strikes, 0x00A3),
    ("Kimahri: Trident",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 3, elemental_strikes, 0x00A4),
    ("Wakka: Tricolor",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 3, elemental_strikes, 0x00A5),
    ("Lulu: Moomba Trio",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 3, elemental_strikes, 0x00A6),
    ("Rikku: Rising Sun",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 3, elemental_strikes, 0x00A7),
    ("Seymour: Tri-Scepter",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 3, elemental_strikes, 0x00A8),

    # 3 status strikes
    ("Tidus: Helter-Skelter",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 3, status_strikes, 0x00A9),
    ("Yuna: Wicked Wand",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 3, status_strikes, 0x00AA),
    ("Auron: Corruptor",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 3, status_strikes, 0x00AB),
    ("Kimahri: Vicious Lance",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 3, status_strikes, 0x00AC),
    ("Wakka: Triple Penalty",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 3, status_strikes, 0x00AD),
    ("Lulu: Abaddon Cait Sith",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 3, status_strikes, 0x00AE),
    ("Rikku: Typhoon Claw",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 3, status_strikes, 0x00AF),
    ("Seymour: Malefic Scepter",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 3, status_strikes, 0x00B0),

    # Magic Counter and either Counterattack or Evade & Counter
    ("Tidus: Vendetta",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 2, [id_to_ability[0x05], [id_to_ability[0x03], id_to_ability[0x04]]], 0x00B1),
    ("Yuna: Nemesis Rod",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 2, [id_to_ability[0x05], [id_to_ability[0x03], id_to_ability[0x04]]], 0x00B2),
    ("Auron: Ashura",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 2, [id_to_ability[0x05], [id_to_ability[0x03], id_to_ability[0x04]]], 0x00B3),
    ("Kimahri: Dragoon Lance",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 2, [id_to_ability[0x05], [id_to_ability[0x03], id_to_ability[0x04]]], 0x00B4),
    ("Wakka: Turnover",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 2, [id_to_ability[0x05], [id_to_ability[0x03], id_to_ability[0x04]]], 0x00B5),
    ("Lulu: Vengeful Cactuar",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 2, [id_to_ability[0x05], [id_to_ability[0x03], id_to_ability[0x04]]], 0x00B6),
    ("Rikku: Untouchable",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 2, [id_to_ability[0x05], [id_to_ability[0x03], id_to_ability[0x04]]], 0x00B7),
    ("Seymour: Nemesis Scepter",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 2, [id_to_ability[0x05], [id_to_ability[0x03], id_to_ability[0x04]]], 0x00B8),

    # Counterattack or Evade & Counter
    ("Tidus: Avenger",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [[id_to_ability[0x03], id_to_ability[0x04]]], 0x00B9),
    ("Yuna: Defender",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [[id_to_ability[0x03], id_to_ability[0x04]]], 0x00BA),
    ("Auron: Kotetsu",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [[id_to_ability[0x03], id_to_ability[0x04]]], 0x00BB),
    ("Kimahri: Rebel Lance",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [[id_to_ability[0x03], id_to_ability[0x04]]], 0x00BC),
    ("Wakka: Rematch",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [[id_to_ability[0x03], id_to_ability[0x04]]], 0x00BD),
    ("Lulu: Raging Cactuar",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [[id_to_ability[0x03], id_to_ability[0x04]]], 0x00BE),
    ("Rikku: Tit-for-Tat",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [[id_to_ability[0x03], id_to_ability[0x04]]], 0x00BF),
    ("Seymour: Karmic Scepter",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [[id_to_ability[0x03], id_to_ability[0x04]]], 0x00C0),

    # Magic Counter
    ("Tidus: Prism Steel",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x05]], 0x00C1),
    ("Yuna: Prism Rod",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x05]], 0x00C2),
    ("Auron: Prism Blade",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x05]], 0x00C3),
    ("Kimahri: Prism Spear",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x05]], 0x00C4),
    ("Wakka: Prism Ball",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x05]], 0x00C5),
    ("Lulu: Prism Cactuar",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x05]], 0x00C6),
    ("Rikku: Prism Claw",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x05]], 0x00C7),
    ("Seymour: Prism Scepter",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x05]], 0x00C8),

    # Magic Booster
    ("Tidus: Mirage Sword",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x06]], 0x00C9),
    ("Yuna: Mirage Rod",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x06]], 0x00CA),
    ("Auron: Mirage Blade",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x06]], 0x00CB),
    ("Kimahri: Mirage Lance",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x06]], 0x00CC),
    ("Wakka: Mirage Ball",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x06]], 0x00CD),
    ("Lulu: Booster Cactuar",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x06]], 0x00CE),
    ("Rikku: Mirage Claw",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x06]], 0x00CF),
    ("Seymour: Mirage Scepter",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x06]], 0x00D0),

    # Alchemy
    ("Tidus: Lifesaver",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x07]], 0x00D1),
    ("Yuna: Healing Rod",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x07]], 0x00D2),
    ("Auron: Lifegiver",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x07]], 0x00D3),
    ("Kimahri: Healer Spear",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x07]], 0x00D4),
    ("Wakka: Comeback",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x07]], 0x00D5),
    ("Lulu: Medical Mog",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x07]], 0x00D6),
    ("Rikku: Survivor",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x07]], 0x00D7),
    ("Seymour: Thaumaturge",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x07]], 0x00D8),

    # First Strike
    ("Tidus: Sonic Steel",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x01]], 0x00D9),
    ("Yuna: Wind Rod",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x01]], 0x00DA),
    ("Auron: Sonic Blade",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x01]], 0x00DB),
    ("Kimahri: Sonic Lance",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x01]], 0x00DC),
    ("Wakka: Breakaway",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x01]], 0x00DD),
    ("Lulu: Swift Cactuar",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x01]], 0x00DE),
    ("Rikku: Vanguard",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x01]], 0x00DF),
    ("Seymour: Sonic Scepter",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x01]], 0x00E0),

    # Initiative
    ("Tidus: Vigilante",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x02]], 0x00E1),
    ("Yuna: Conductor",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x02]], 0x00E2),
    ("Auron: Sentry",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x02]], 0x00E3),
    ("Kimahri: Detector",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x02]], 0x00E4),
    ("Wakka: First Goal",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x02]], 0x00E5),
    ("Lulu: Cactuar Spy",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x02]], 0x00E6),
    ("Rikku: Sonar",                 ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x02]], 0x00E7),
    ("Seymour: Quick Gambit",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x02]], 0x00E8),

    # Deathstrike
    ("Tidus: Dance Macabre",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x2E]], 0x00E9),
    ("Yuna: Punisher",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x2E]], 0x00EA),
    ("Auron: Assassin Blade",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x2E]], 0x00EB),
    ("Kimahri: Thanatos Lance",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x2E]], 0x00EC),
    ("Wakka: Sudden Death",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x2E]], 0x00ED),
    ("Lulu: Wicked Cait Sith",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x2E]], 0x00EE),
    ("Rikku: Executioner",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x2E]], 0x00EF),
    ("Seymour: Grim Embrace",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x2E]], 0x00F0),

    # Slowstrike
    ("Tidus: Largamente",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x4A]], 0x00F1),
    ("Yuna: Impasse",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x4A]], 0x00F2),
    ("Auron: Blockade",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x4A]], 0x00F3),
    ("Kimahri: Net Spear",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x4A]], 0x00F4),
    ("Wakka: Timeout",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x4A]], 0x00F5),
    ("Lulu: Chronos Cait Sith",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x4A]], 0x00F6),
    ("Rikku: Clockwork",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x4A]], 0x00F7),
    ("Seymour: Halting Grace",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x4A]], 0x00F8),

    # Stonestrike
    ("Tidus: Gravestone",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x36]], 0x00F9),
    ("Yuna: Calcite Staff",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x36]], 0x00FA),
    ("Auron: Stillblade",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x36]], 0x00FB),
    ("Kimahri: Rock Buster",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x36]], 0x00FC),
    ("Wakka: Stone Cold",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x36]], 0x00FD),
    ("Lulu: Stone Cait Sith",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x36]], 0x00FE),
    ("Rikku: Colossus",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x36]], 0x00FF),
    ("Seymour: Earth Breaker",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x36]], 0x0100),

    # Poisonstrike
    ("Tidus: Sidewinder",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x3A]], 0x0101),
    ("Yuna: Bizarre Staff",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x3A]], 0x0102),
    ("Auron: Venomous Blade",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x3A]], 0x0103),
    ("Kimahri: Venom Spike",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x3A]], 0x0104),
    ("Wakka: Violation",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x3A]], 0x0105),
    ("Lulu: Toxic Cait Sith",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x3A]], 0x0106),
    ("Rikku: Manticore Claw",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x3A]], 0x0107),
    ("Seymour: Serpent's Fang",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x3A]], 0x0108),

    # Sleepstrike
    ("Tidus: Nightmare",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x3E]], 0x0109),
    ("Yuna: Staff of Thorns",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x3E]], 0x010A),
    ("Auron: Dozing Blade",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x3E]], 0x010B),
    ("Kimahri: Hypnos Spear",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x3E]], 0x010C),
    ("Wakka: Sleeper",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x3E]], 0x010D),
    ("Lulu: Dreamy Cait Sith",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x3E]], 0x010E),
    ("Rikku: Lights Out",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x3E]], 0x010F),
    ("Seymour: Eternal Slumber",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x3E]], 0x0110),

    # Silencestrike
    ("Tidus: Mage Masher",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x42]], 0x0111),
    ("Yuna: Reticent Staff",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x42]], 0x0112),
    ("Auron: Tacit Blade",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x42]], 0x0113),
    ("Kimahri: Mage Hunter",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x42]], 0x0114),
    ("Wakka: Muffler",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x42]], 0x0115),
    ("Lulu: Mute Cait Sith",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x42]], 0x0116),
    ("Rikku: Mage Husher",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x42]], 0x0117),
    ("Seymour: Inhibitor",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x42]], 0x0118),

    # Darkstrike
    ("Tidus: Nightbringer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x46]], 0x0119),
    ("Yuna: Darkness Staff",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x46]], 0x011A),
    ("Auron: Dark Blade",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x46]], 0x011B),
    ("Kimahri: Darkbringer",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x46]], 0x011C),
    ("Wakka: Blackout",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x46]], 0x011D),
    ("Lulu: Dark Cait Sith",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x46]], 0x011E),
    ("Rikku: Jammer",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x46]], 0x011F),
    ("Seymour: Nightfall",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x46]], 0x0120),

    # 3 Strength +%s
    ("Tidus: Knight Sword",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 3, strength_abilities, 0x0121),
    ("Yuna: Monk Staff",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 3, strength_abilities, 0x0122),
    ("Auron: Ogre Blade",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 3, strength_abilities, 0x0123),
    ("Kimahri: Knight Lance",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 3, strength_abilities, 0x0124),
    ("Wakka: Power Play",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 3, strength_abilities, 0x0125),
    ("Lulu: Power Mog",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 3, strength_abilities, 0x0126),
    ("Rikku: Iron Claw",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 3, strength_abilities, 0x0127),
    ("Seymour: Monk's Scepter",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 3, strength_abilities, 0x0128),

    # 3 Magic +%s
    ("Tidus: Wizard Sword",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 3, magic_abilities, 0x0129),
    ("Yuna: Mage’s Staff",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 3, magic_abilities, 0x012A),
    ("Auron: Djinn Blade",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 3, magic_abilities, 0x012B),
    ("Kimahri: Wizard Lance",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 3, magic_abilities, 0x012C),
    ("Wakka: Virtuoso",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 3, magic_abilities, 0x012D),
    ("Lulu: Magician Mog",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 3, magic_abilities, 0x012E),
    ("Rikku: The Ogre",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 3, magic_abilities, 0x012F),
    ("Seymour: Priest's Scepter",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 3, magic_abilities, 0x0130),

    # 2 elemental strikes
    ("Tidus: Double-Edge",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 2, elemental_strikes, 0x0131),
    ("Yuna: Dual Rod",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 2, elemental_strikes, 0x0132),
    ("Auron: Dual Blade",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 2, elemental_strikes, 0x0133),
    ("Kimahri: Twin Lance",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 2, elemental_strikes, 0x0134),
    ("Wakka: Double Header",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 2, elemental_strikes, 0x0135),
    ("Lulu: Moomba Duo",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 2, elemental_strikes, 0x0136),
    ("Rikku: Dual Claw",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 2, elemental_strikes, 0x0137),
    ("Seymour: Dual Scepter",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 2, elemental_strikes, 0x0138),

    # 2 status touches
    ("Tidus: Razzmatazz",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 2, status_touches, 0x0139),
    ("Yuna: Ominous Rod",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 2, status_touches, 0x013A),
    ("Auron: Chaos Blade",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 2, status_touches, 0x013B),
    ("Kimahri: Calamity Spear",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 2, status_touches, 0x013C),
    ("Wakka: Double Penalty",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 2, status_touches, 0x013D),
    ("Lulu: Ominous Cait Sith",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 2, status_touches, 0x013E),
    ("Rikku: Hurricane Claw",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 2, status_touches, 0x013F),
    ("Seymour: Ominous Scepter",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 2, status_touches, 0x0140),

    # Deathtouch
    ("Tidus: Deathbringer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x2F]], 0x0141),
    ("Yuna: Death Wand",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x2F]], 0x0142),
    ("Auron: Critical Blade",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x2F]], 0x0143),
    ("Kimahri: Matador Spear",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x2F]], 0x0144),
    ("Wakka: Rough Play",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x2F]], 0x0145),
    ("Lulu: Fatal Cait Sith",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x2F]], 0x0146),
    ("Rikku: Ninja Claw",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x2F]], 0x0147),
    ("Seymour: Atrophy Scepter",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x2F]], 0x0148),

    # Slowtouch
    ("Tidus: Stunning Steel",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x4B]], 0x0149),
    ("Yuna: Entangling Rod",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x4B]], 0x014A),
    ("Auron: Stunner",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x4B]], 0x014B),
    ("Kimahri: Web Lance",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x4B]], 0x014C),
    ("Wakka: Delay of Game",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x4B]], 0x014D),
    ("Lulu: Late Cait Sith",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x4B]], 0x014E),
    ("Rikku: Clock Hand",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x4B]], 0x014F),
    ("Seymour: Languid Scepter",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x4B]], 0x0150),

    # Stonetouch
    ("Tidus: Basilisk Steel",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x37]], 0x0151),
    ("Yuna: Break Rod",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x37]], 0x0152),
    ("Auron: Gorgon Gaze",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x37]], 0x0153),
    ("Kimahri: Break Lance",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x37]], 0x0154),
    ("Wakka: T.K.O.",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x37]], 0x0155),
    ("Lulu: Fossil Cait Sith",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x37]], 0x0156),
    ("Rikku: Break Knuckles",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x37]], 0x0157),
    ("Seymour: Break Scepter",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x37]], 0x0158),

    # Poisontouch
    ("Tidus: Poison Steel",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x3B]], 0x0159),
    ("Yuna: Beladonna Wand",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x3B]], 0x015A),
    ("Auron: Spider’s Kiss",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x3B]], 0x015B),
    ("Kimahri: Snakehead",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x3B]], 0x015C),
    ("Wakka: Rulebreaker",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x3B]], 0x015D),
    ("Lulu: Noxious Cait Sith",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x3B]], 0x015E),
    ("Rikku: Poison Claw",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x3B]], 0x015F),
    ("Seymour: Miasma Scepter",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x3B]], 0x0160),

    # Sleeptouch
    ("Tidus: Lullaby Steel",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x3F]], 0x0161),
    ("Yuna: Lullaby Rod",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x3F]], 0x0162),
    ("Auron: Peaceful Slumber",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x3F]], 0x0163),
    ("Kimahri: Dream Lance",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x3F]], 0x0164),
    ("Wakka: Dream Team",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x3F]], 0x0165),
    ("Lulu: Sleepy Cait Sith",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x3F]], 0x0166),
    ("Rikku: Daydreamer",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x3F]], 0x0167),
    ("Seymour: Hypno Scepter",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x3F]], 0x0168),

    # Silencetouch
    ("Tidus: Muted Steel",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x43]], 0x0169),
    ("Yuna: Rod of Silence",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x43]], 0x016A),
    ("Auron: Soundless Scream",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x43]], 0x016B),
    ("Kimahri: Silent Spear",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x43]], 0x016C),
    ("Wakka: Noisebreaker",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x43]], 0x016D),
    ("Lulu: Quiet Cait Sith",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x43]], 0x016E),
    ("Rikku: Tongue Holder",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x43]], 0x016F),
    ("Seymour: Tranquil Scepter",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x43]], 0x0170),

    # Darktouch
    ("Tidus: Twilight Steel",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x47]], 0x0171),
    ("Yuna: Rod of Darkness",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x47]], 0x0172),
    ("Auron: Blurry Moon",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x47]], 0x0173),
    ("Kimahri: Dusk Lance",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x47]], 0x0174),
    ("Wakka: Blind Pass",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x47]], 0x0175),
    ("Lulu: Blinding Cait Sith",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x47]], 0x0176),
    ("Rikku: Eye Poker",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x47]], 0x0177),
    ("Seymour: Twilight Scepter",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x47]], 0x0178),

    # Sensor
    ("Tidus: Hunter’s Sword",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x00]], 0x0179),
    ("Yuna: Rod of Wisdom",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x00]], 0x017A),
    ("Auron: Hunter’s Blade",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x00]], 0x017B),
    ("Kimahri: Hunter’s Spear",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x00]], 0x017C),
    ("Wakka: Scout",                 ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x00]], 0x017D),
    ("Lulu: Cactuar Scope",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x00]], 0x017E),
    ("Rikku: Hawkeye",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x00]], 0x017F),
    ("Seymour: Scout Scepter",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x00]], 0x0180),

    # Firestrike
    ("Tidus: Flametongue",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x1E]], 0x0181),
    ("Yuna: Rod of Fire",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x1E]], 0x0182),
    ("Auron: Fire Blade",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x1E]], 0x0183),
    ("Kimahri: Heat Lance",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x1E]], 0x0184),
    ("Wakka: Fire Ball",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x1E]], 0x0185),
    ("Lulu: Fire Moomba",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x1E]], 0x0186),
    ("Rikku: Hot Knuckles",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x1E]], 0x0187),
    ("Seymour: Flame Scepter",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x1E]], 0x0188),

    # Icestrike
    ("Tidus: Ice Brand",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x22]], 0x0189),
    ("Yuna: Rod of Ice",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x22]], 0x018A),
    ("Auron: Frost Blade",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x22]], 0x018B),
    ("Kimahri: Ice Lance",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x22]], 0x018C),
    ("Wakka: Ice Ball",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x22]], 0x018D),
    ("Lulu: Ice Moomba",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x22]], 0x018E),
    ("Rikku: Ice Claw",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x22]], 0x018F),
    ("Seymour: Frost Scepter",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x22]], 0x0190),

    # Lightningstrike
    ("Tidus: Lightning Steel",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x26]], 0x0191),
    ("Yuna: Rod of Lightning",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x26]], 0x0192),
    ("Auron: Thunder Blade",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x26]], 0x0193),
    ("Kimahri: Thunder Spear",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x26]], 0x0194),
    ("Wakka: Thunder Ball",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x26]], 0x0195),
    ("Lulu: Thunder Moomba",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x26]], 0x0196),
    ("Rikku: Shocking Fist",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x26]], 0x0197),
    ("Seymour: Blitz Scepter",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x26]], 0x0198),

    # Waterstrike
    ("Tidus: Liquid Steel",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x2A]], 0x0199),
    ("Yuna: Rod of Water",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x2A]], 0x019A),
    ("Auron: Water Blade",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x2A]], 0x019B),
    ("Kimahri: Tidal Spear",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x2A]], 0x019C),
    ("Wakka: Water Ball",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x2A]], 0x019D),
    ("Lulu: Water Moomba",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x2A]], 0x019E),
    ("Rikku: Tidal Knuckles",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x2A]], 0x019F),
    ("Seymour: Flood Scepter",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x2A]], 0x01A0),

    # Distill Power
    # Distill Mana
    # Distill Speed
    # Distill Ability

    # 4 slots
    ("Tidus: Variable Steel",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 4, [], 0x01A1),
    ("Yuna: Malleable Staff",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 4, [], 0x01A2),
    ("Auron: Shiranui",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 4, [], 0x01A3),
    ("Kimahri: Shapeshifter",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 4, [], 0x01A4),
    ("Wakka: All-Rounder",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 4, [], 0x01A5),
    ("Lulu: Morphing Mog",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 4, [], 0x01A6),
    ("Rikku: Flexible Arm",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 4, [], 0x01A7),
    ("Seymour: Futile Scepter",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 4, [], 0x01A8),

    # 1 Magic +%s and 1 Strength +%s
    ("Tidus: Force Sabre",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 2, [magic_abilities, strength_abilities], 0x01A9),
    ("Yuna: Force Rod",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 2, [magic_abilities, strength_abilities], 0x01AA),
    ("Auron: Basara Blade",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 2, [magic_abilities, strength_abilities], 0x01AB),
    ("Kimahri: Force Lance",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 2, [magic_abilities, strength_abilities], 0x01AC),
    ("Wakka: Ovation",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 2, [magic_abilities, strength_abilities], 0x01AD),
    ("Lulu: Moomba Force",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 2, [magic_abilities, strength_abilities], 0x01AE),
    ("Rikku: Force Knuckles",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 2, [magic_abilities, strength_abilities], 0x01AF),
    ("Seymour: Force Scepter",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 2, [magic_abilities, strength_abilities], 0x01B0),

    # 2 slots
    ("Tidus: Baroque Sword",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 2, [], 0x01B1),
    ("Yuna: Ductile Rod",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 2, [], 0x01B2),
    ("Auron: Shimmering Blade",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 2, [], 0x01B3),
    ("Kimahri: Halberd",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 2, [], 0x01B4),
    ("Wakka: Switch Hitter",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 2, [], 0x01B5),
    ("Lulu: Variable Mog",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 2, [], 0x01B6),
    ("Rikku: Devastator",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 2, [], 0x01B7),
    ("Seymour: Vain Scepter",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 2, [], 0x01B8),

    # Magic +10% or Magic +20%
    ("Tidus: Sorcery Sword",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, magic_abilities[2:], 0x01B9),
    ("Yuna: Sorcery Rod",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, magic_abilities[2:], 0x01BA),
    ("Auron: Spiritual Blade",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, magic_abilities[2:], 0x01BB),
    ("Kimahri: Magic Lance",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, magic_abilities[2:], 0x01BC),
    ("Wakka: Trickster",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, magic_abilities[2:], 0x01BD),
    ("Lulu: Moomba Mage",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, magic_abilities[2:], 0x01BE),
    ("Rikku: Magic Knuckles",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, magic_abilities[2:], 0x01BF),
    ("Seymour: Sorcery Scepter",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, magic_abilities[2:], 0x01C0),

    # Strength +10% or Strength +20%
    ("Tidus: Soldier’s Sabre",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, strength_abilities[2:], 0x01C1),
    ("Yuna: Full Metal Rod",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, strength_abilities[2:], 0x01C2),
    ("Auron: Knight Blade",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, strength_abilities[2:], 0x01C3),
    ("Kimahri: Full Metal Spear",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, strength_abilities[2:], 0x01C4),
    ("Wakka: Striker",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, strength_abilities[2:], 0x01C5),
    ("Lulu: Moomba Warrior",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, strength_abilities[2:], 0x01C6),
    ("Rikku: Buster Knuckles",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, strength_abilities[2:], 0x01C7),
    ("Seymour: Decimator Scepter",   ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, strength_abilities[2:], 0x01C8),

    # Magic +5%
    ("Tidus: Rune Steel",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [magic_abilities[1]], 0x01C9),
    ("Yuna: Rune Rod",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [magic_abilities[1]], 0x01CA),
    ("Auron: Rune Blade",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [magic_abilities[1]], 0x01CB),
    ("Kimahri: Rune Lance",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [magic_abilities[1]], 0x01CC),
    ("Wakka: Rune Ball",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [magic_abilities[1]], 0x01CD),
    ("Lulu: Rune Mog",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [magic_abilities[1]], 0x01CE),
    ("Rikku: Magic Claw",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [magic_abilities[1]], 0x01CF),
    ("Seymour: Rune Scepter",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [magic_abilities[1]], 0x01D0),

    # Magic +3%
    ("Tidus: Enchanted Sword",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [magic_abilities[0]], 0x01D1),
    ("Yuna: Enchanted Rod",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [magic_abilities[0]], 0x01D2),
    ("Auron: Magic Blade",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [magic_abilities[0]], 0x01D3),
    ("Kimahri: Enchanted Lance",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [magic_abilities[0]], 0x01D4),
    ("Wakka: Magic Ball",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [magic_abilities[0]], 0x01D5),
    ("Lulu: Magical Mog",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [magic_abilities[0]], 0x01D6),
    ("Rikku: Magic Glove",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [magic_abilities[0]], 0x01D7),
    ("Seymour: Enchanted Scepter",   ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [magic_abilities[0]], 0x01D8),

    # Strength +5%
    ("Tidus: Fencing Sabre",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [strength_abilities[1]], 0x01D9),
    ("Yuna: Rod of Striking",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [strength_abilities[1]], 0x01DA),
    ("Auron: Warblade",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [strength_abilities[1]], 0x01DB),
    ("Kimahri: Striking Spear",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [strength_abilities[1]], 0x01DC),
    ("Wakka: Hyper Ball",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [strength_abilities[1]], 0x01DD),
    ("Lulu: Buster Mog",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [strength_abilities[1]], 0x01DE),
    ("Rikku: Buster Claw",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [strength_abilities[1]], 0x01DF),
    ("Seymour: Buster Scepter",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [strength_abilities[1]], 0x01E0),

    # Strength +3%
    ("Tidus: Warrior’s Sword",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [strength_abilities[0]], 0x01E1),
    ("Yuna: Rod of Beating",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [strength_abilities[0]], 0x01E2),
    ("Auron: Nodachi",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [strength_abilities[0]], 0x01E3),
    ("Kimahri: Heavy Spear",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [strength_abilities[0]], 0x01E4),
    ("Wakka: Power Ball",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [strength_abilities[0]], 0x01E5),
    ("Lulu: Attack Mog",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [strength_abilities[0]], 0x01E6),
    ("Rikku: Buster Glove",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [strength_abilities[0]], 0x01E7),
    ("Seymour: Ruin Scepter",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [strength_abilities[0]], 0x01E8),

    # Piercing
    ("Tidus: Slasher",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 1, [id_to_ability[0x0B]], 0x01E9),
    ("Yuna: Spiked Rod",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 1, [id_to_ability[0x0B]], 0x01EA),
    ("Auron: Katana",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 1, [id_to_ability[0x0B]], 0x01EB),
    ("Kimahri: Harpoon",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 1, [id_to_ability[0x0B]], 0x01EC),
    ("Wakka: Center Forward",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 1, [id_to_ability[0x0B]], 0x01ED),
    ("Lulu: Stinger Mog",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 1, [id_to_ability[0x0B]], 0x01EE),
    ("Rikku: Barbed Knuckles",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 1, [id_to_ability[0x0B]], 0x01EF),
    ("Seymour: Spiked Scepter",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 1, [id_to_ability[0x0B]], 0x01F0),

    # Else
    ("Tidus: Longsword",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.WEAPON, 0, [], 0x01F1),
    ("Yuna: Staff",                  ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.WEAPON, 0, [], 0x01F2),
    ("Auron: Dull Blade",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.WEAPON, 0, [], 0x01F3),
    ("Kimahri: Spear",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.WEAPON, 0, [], 0x01F4),
    ("Wakka: Official Ball",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.WEAPON, 0, [], 0x01F5),
    ("Lulu: Moogle",                 ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.WEAPON, 0, [], 0x01F6),
    ("Rikku: Claw",                  ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.WEAPON, 0, [], 0x01F7),
    ("Seymour: Scepter",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.WEAPON, 0, [], 0x01F8),


    ## Armor

    # Break HP Limit and Break MP Limit
    ("Tidus: Endless Road",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 2, [id_to_ability[0x17], id_to_ability[0x18]], 0x01F9),
    ("Yuna: Solomon Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 2, [id_to_ability[0x17], id_to_ability[0x18]], 0x01FA),
    ("Auron: Overlord",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 2, [id_to_ability[0x17], id_to_ability[0x18]], 0x01FB),
    ("Kimahri: Pride of the Ronso",  ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 2, [id_to_ability[0x17], id_to_ability[0x18]], 0x01FC),
    ("Wakka: Indomitable",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 2, [id_to_ability[0x17], id_to_ability[0x18]], 0x01FD),
    ("Lulu: Samantha Soul",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 2, [id_to_ability[0x17], id_to_ability[0x18]], 0x01FE),
    ("Rikku: Dreadnought",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 2, [id_to_ability[0x17], id_to_ability[0x18]], 0x01FF),
    ("Seymour: Resolute",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 2, [id_to_ability[0x17], id_to_ability[0x18]], 0x0200),

    # Ribbon
    ("Tidus: Sanctuary",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x80]], 0x0201),
    ("Yuna: Holy Ring",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x80]], 0x0202),
    ("Auron: Solidity",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x80]], 0x0203),
    ("Kimahri: Acropolis",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x80]], 0x0204),
    ("Wakka: Shutout",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x80]], 0x0205),
    ("Lulu: Eternity",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x80]], 0x0206),
    ("Rikku: Impervious",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x80]], 0x0207),
    ("Seymour: Absolution",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x80]], 0x0208),

    # Break HP Limit
    ("Tidus: Genji Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x17]], 0x0209),
    ("Yuna: Arcane Ring",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x17]], 0x020A),
    ("Auron: Genji Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x17]], 0x020B),
    ("Kimahri: Genji Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x17]], 0x020C),
    ("Wakka: Super Goalie",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x17]], 0x020D),
    ("Lulu: Minerva Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x17]], 0x020E),
    ("Rikku: Atlas",                 ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x17]], 0x020F),
    ("Seymour: Arcane Circlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x17]], 0x0210),

    # Break MP Limit
    ("Tidus: Emblem",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x18]], 0x0211),
    ("Yuna: Mythical Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x18]], 0x0212),
    ("Auron: Dragon Lord",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x18]], 0x0213),
    ("Kimahri: Sage’s Armlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x18]], 0x0214),
    ("Wakka: High Spirits",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x18]], 0x0215),
    ("Lulu: Mythical Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x18]], 0x0216),
    ("Rikku: Celestial",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x18]], 0x0217),
    ("Seymour: Mythical Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x18]], 0x0218),

    # 4 elemental ”Eater” abilities
    ("Tidus: Crystal Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 4, elemental_eaters, 0x0219),
    ("Yuna: Sophia Ring",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 4, elemental_eaters, 0x021A),
    ("Auron: Glutton",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 4, elemental_eaters, 0x021B),
    ("Kimahri: Crystal Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 4, elemental_eaters, 0x021C),
    ("Wakka: Final Four",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 4, elemental_eaters, 0x021D),
    ("Lulu: Draupnir",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 4, elemental_eaters, 0x021E),
    ("Rikku: Invincible",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 4, elemental_eaters, 0x021F),
    ("Seymour: Crystal Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 4, elemental_eaters, 0x0220),

    # 4 elemental ”proof” abilities
    ("Tidus: Aegis Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 4, elemental_proofs, 0x0221),
    ("Yuna: Aegis Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 4, elemental_proofs, 0x0222),
    ("Auron: Resistant",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 4, elemental_proofs, 0x0223),
    ("Kimahri: Aegis Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 4, elemental_proofs, 0x0224),
    ("Wakka: Great Four",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 4, elemental_proofs, 0x0225),
    ("Lulu: Aegis Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 4, elemental_proofs, 0x0226),
    ("Rikku: Armada",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 4, elemental_proofs, 0x0227),
    ("Seymour: Aegis Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 4, elemental_proofs, 0x0228),

    # Auto-Reflect, Auto-Regen, Auto-Protect, and Auto-Shell
    ("Tidus: Golem Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 4, [id_to_ability[0x58], id_to_ability[0x57], id_to_ability[0x55], id_to_ability[0x54]], 0x0229),
    ("Yuna: Sheltering Ring",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 4, [id_to_ability[0x58], id_to_ability[0x57], id_to_ability[0x55], id_to_ability[0x54]], 0x022A),
    ("Auron: Warder",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 4, [id_to_ability[0x58], id_to_ability[0x57], id_to_ability[0x55], id_to_ability[0x54]], 0x022B),
    ("Kimahri: Adamantite",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 4, [id_to_ability[0x58], id_to_ability[0x57], id_to_ability[0x55], id_to_ability[0x54]], 0x022C),
    ("Wakka: The Guardian",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 4, [id_to_ability[0x58], id_to_ability[0x57], id_to_ability[0x55], id_to_ability[0x54]], 0x022D),
    ("Lulu: Precious Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 4, [id_to_ability[0x58], id_to_ability[0x57], id_to_ability[0x55], id_to_ability[0x54]], 0x022E),
    ("Rikku: Triumph",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 4, [id_to_ability[0x58], id_to_ability[0x57], id_to_ability[0x55], id_to_ability[0x54]], 0x022F),
    ("Seymour: Unwavering",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 4, [id_to_ability[0x58], id_to_ability[0x57], id_to_ability[0x55], id_to_ability[0x54]], 0x0230),

    # Auto-Phoenix, Auto-Med, and Auto-Potion
    ("Tidus: Revive Shield",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 3, [id_to_ability[0x0A], id_to_ability[0x09], id_to_ability[0x08]], 0x0231),
    ("Yuna: Savior Ring",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 3, [id_to_ability[0x0A], id_to_ability[0x09], id_to_ability[0x08]], 0x0232),
    ("Auron: Immortal",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 3, [id_to_ability[0x0A], id_to_ability[0x09], id_to_ability[0x08]], 0x0233),
    ("Kimahri: Orichalcum",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 3, [id_to_ability[0x0A], id_to_ability[0x09], id_to_ability[0x08]], 0x0234),
    ("Wakka: Automatic",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 3, [id_to_ability[0x0A], id_to_ability[0x09], id_to_ability[0x08]], 0x0235),
    ("Lulu: Imperial Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 3, [id_to_ability[0x0A], id_to_ability[0x09], id_to_ability[0x08]], 0x0236),
    ("Rikku: Intrepid",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 3, [id_to_ability[0x0A], id_to_ability[0x09], id_to_ability[0x08]], 0x0237),
    ("Seymour: Renatus",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 3, [id_to_ability[0x0A], id_to_ability[0x09], id_to_ability[0x08]], 0x0238),

    # Auto-Potion and Auto-Med
    ("Tidus: Rescue Shield",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 2, [id_to_ability[0x08], id_to_ability[0x09]], 0x0239),
    ("Yuna: Healing Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 2, [id_to_ability[0x08], id_to_ability[0x09]], 0x023A),
    ("Auron: Healer",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 2, [id_to_ability[0x08], id_to_ability[0x09]], 0x023B),
    ("Kimahri: Safe Passage",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 2, [id_to_ability[0x08], id_to_ability[0x09]], 0x023C),
    ("Wakka: First Aid",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 2, [id_to_ability[0x08], id_to_ability[0x09]], 0x023D),
    ("Lulu: Auto Bangle",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 2, [id_to_ability[0x08], id_to_ability[0x09]], 0x023E),
    ("Rikku: Goliath",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 2, [id_to_ability[0x08], id_to_ability[0x09]], 0x023F),
    ("Seymour: Restorative Circlet", ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 2, [id_to_ability[0x08], id_to_ability[0x09]], 0x0240),

    # 4 status ”proof” abilities
    ("Tidus: Paladin Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 4, status_proofs, 0x0241),
    ("Yuna: Forbidding Ring",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 4, status_proofs, 0x0242),
    ("Auron: Undefeated",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 4, status_proofs, 0x0243),
    ("Kimahri: Ronso Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 4, status_proofs, 0x0244),
    ("Wakka: Keeper",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 4, status_proofs, 0x0245),
    ("Lulu: Black Ribbon",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 4, status_proofs, 0x0246),
    ("Rikku: Argonaut",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 4, status_proofs, 0x0247),
    ("Seymour: Omnis",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 4, status_proofs, 0x0248),

    # 4 Defense +%s
    ("Tidus: Diamond Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 4, defense_abilities, 0x0249),
    ("Yuna: Diamond Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 4, defense_abilities, 0x024A),
    ("Auron: Diamond Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 4, defense_abilities, 0x024B),
    ("Kimahri: Diamond Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 4, defense_abilities, 0x024C),
    ("Wakka: Diamond Armguard",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 4, defense_abilities, 0x024D),
    ("Lulu: Diamond Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 4, defense_abilities, 0x024E),
    ("Rikku: Diamond Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 4, defense_abilities, 0x024F),
    ("Seymour: Diamond Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 4, defense_abilities, 0x0250),

    # 4 Magic Def +%s
    ("Tidus: Ruby Shield",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 4, magic_defense_abilities, 0x0251),
    ("Yuna: Ruby Ring",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 4, magic_defense_abilities, 0x0252),
    ("Auron: Ruby Bracer",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 4, magic_defense_abilities, 0x0253),
    ("Kimahri: Ruby Armlet",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 4, magic_defense_abilities, 0x0254),
    ("Wakka: Ruby Armguard",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 4, magic_defense_abilities, 0x0255),
    ("Lulu: Ruby Bangle",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 4, magic_defense_abilities, 0x0256),
    ("Rikku: Ruby Targe",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 4, magic_defense_abilities, 0x0257),
    ("Seymour: Ruby Circlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 4, magic_defense_abilities, 0x0258),

    # 4 HP +%s
    ("Tidus: Dynasty Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 4, hp_abilities, 0x0259),
    ("Yuna: Fortitude Ring",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 4, hp_abilities, 0x025A),
    ("Auron: Battle Bracer",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 4, hp_abilities, 0x025B),
    ("Kimahri: Enhanced Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 4, hp_abilities, 0x025C),
    ("Wakka: Power Ace",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 4, hp_abilities, 0x025D),
    ("Lulu: Queen’s Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 4, hp_abilities, 0x025E),
    ("Rikku: Warlord",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 4, hp_abilities, 0x025F),
    ("Seymour: Empowered Circlet",   ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 4, hp_abilities, 0x0260),

    # 4 MP +%s
    ("Tidus: Magister Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 4, mp_abilities, 0x0261),
    ("Yuna: Magical Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 4, mp_abilities, 0x0262),
    ("Auron: Magical Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 4, mp_abilities, 0x0263),
    ("Kimahri: Magical Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 4, mp_abilities, 0x0264),
    ("Wakka: Magic Ace",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 4, mp_abilities, 0x0265),
    ("Lulu: Magister Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 4, mp_abilities, 0x0266),
    ("Rikku: Dominator",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 4, mp_abilities, 0x0267),
    ("Seymour: Magical Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 4, mp_abilities, 0x0268),

    # Master Thief
    ("Tidus: Collector’s Shield",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x16]], 0x0269),
    ("Yuna: Collector Ring",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x16]], 0x026A),
    ("Auron: Collector Bracer",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x16]], 0x026B),
    ("Kimahri: Collector Armlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x16]], 0x026C),
    ("Wakka: Best Play",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x16]], 0x026D),
    ("Lulu: Collector Bangle",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x16]], 0x026E),
    ("Rikku: Buccaneer",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x16]], 0x026F),
    ("Seymour: Collector Circlet",   ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x16]], 0x0270),

    # Pickpocket
    ("Tidus: Treasure Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x15]], 0x0271),
    ("Yuna: Treasure Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x15]], 0x0272),
    ("Auron: Treasure Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x15]], 0x0273),
    ("Kimahri: Treasure Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x15]], 0x0274),
    ("Wakka: Great Play",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x15]], 0x0275),
    ("Lulu: Treasure Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x15]], 0x0276),
    ("Rikku: Corsair",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x15]], 0x0277),
    ("Seymour: Treasure Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x15]], 0x0278),

    # HP Stroll and MP Stroll
    ("Tidus: Shield of Hope",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 2, [id_to_ability[0x1B], id_to_ability[0x1C]], 0x0279),
    ("Yuna: Ring of Hope",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 2, [id_to_ability[0x1B], id_to_ability[0x1C]], 0x027A),
    ("Auron: Bracer of Hope",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 2, [id_to_ability[0x1B], id_to_ability[0x1C]], 0x027B),
    ("Kimahri: Armlet of Hope",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 2, [id_to_ability[0x1B], id_to_ability[0x1C]], 0x027C),
    ("Wakka: Benchwarmer",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 2, [id_to_ability[0x1B], id_to_ability[0x1C]], 0x027D),
    ("Lulu: Bangle of Hope",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 2, [id_to_ability[0x1B], id_to_ability[0x1C]], 0x027E),
    ("Rikku: Targe of Hope",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 2, [id_to_ability[0x1B], id_to_ability[0x1C]], 0x027F),
    ("Seymour: Circlet of Hope",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 2, [id_to_ability[0x1B], id_to_ability[0x1C]], 0x0280),

    # 4 ”Auto-” abilities
    ("Tidus: Assault Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 4, auto_abilities, 0x0281),
    ("Yuna: Assault Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 4, auto_abilities, 0x0282),
    ("Auron: Assault Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 4, auto_abilities, 0x0283),
    ("Kimahri: Assault Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 4, auto_abilities, 0x0284),
    ("Wakka: Triple Save",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 4, auto_abilities, 0x0285),
    ("Lulu: Assault Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 4, auto_abilities, 0x0286),
    ("Rikku: Assault Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 4, auto_abilities, 0x0287),
    ("Seymour: Assault Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 4, auto_abilities, 0x0288),

    # 3 elemental ”Eater” abilities
    ("Tidus: Phantom Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 3, elemental_eaters, 0x0289),
    ("Yuna: Phantom Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 3, elemental_eaters, 0x028A),
    ("Auron: Phantom Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 3, elemental_eaters, 0x028B),
    ("Kimahri: Phantom Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 3, elemental_eaters, 0x028C),
    ("Wakka: Element Save",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 3, elemental_eaters, 0x028D),
    ("Lulu: Phantom Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 3, elemental_eaters, 0x028E),
    ("Rikku: Phantom Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 3, elemental_eaters, 0x028F),
    ("Seymour: Phantom Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 3, elemental_eaters, 0x0290),

    # HP Stroll
    ("Tidus: Recovery Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x1B]], 0x0291),
    ("Yuna: Recovery Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x1B]], 0x0292),
    ("Auron: Recovery Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x1B]], 0x0293),
    ("Kimahri: Recovery Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x1B]], 0x0294),
    ("Wakka: Armsling",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x1B]], 0x0295),
    ("Lulu: Recovery Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x1B]], 0x0296),
    ("Rikku: Recovery Targe",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x1B]], 0x0297),
    ("Seymour: Recovery Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x1B]], 0x0298),

    # MP Stroll
    ("Tidus: Spiritual Shield",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x1C]], 0x0299),
    ("Yuna: Spiritual Ring",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x1C]], 0x029A),
    ("Auron: Spiritual Bracer",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x1C]], 0x029B),
    ("Kimahri: Spiritual Armlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x1C]], 0x029C),
    ("Wakka: Spiritual Armguard",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x1C]], 0x029D),
    ("Lulu: Spiritual Bangle",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x1C]], 0x029E),
    ("Rikku: Spiritual Targe",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x1C]], 0x029F),
    ("Seymour: Spiritual Circlet",   ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x1C]], 0x02A0),

    # Auto-Phoenix
    ("Tidus: Phoenix Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x0A]], 0x02A1),
    ("Yuna: Phoenix Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x0A]], 0x02A2),
    ("Auron: Phoenix Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x0A]], 0x02A3),
    ("Kimahri: Phoenix Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x0A]], 0x02A4),
    ("Wakka: Miracle Comeback",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x0A]], 0x02A5),
    ("Lulu: Phoenix Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x0A]], 0x02A6),
    ("Rikku: Phoenix Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x0A]], 0x02A7),
    ("Seymour: Phoenix Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x0A]], 0x02A8),

    # Auto-Med
    ("Tidus: Curative Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x09]], 0x02A9),
    ("Yuna: Curative Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x09]], 0x02AA),
    ("Auron: Curative Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x09]], 0x02AB),
    ("Kimahri: Curative Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x09]], 0x02AC),
    ("Wakka: Top Shape",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x09]], 0x02AD),
    ("Lulu: Curative Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x09]], 0x02AE),
    ("Rikku: Curative Targe",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x09]], 0x02AF),
    ("Seymour: Curative Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x09]], 0x02B0),

    # 4 SOS elemental ”Nul” abilities
    ("Tidus: Rainbow Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 4, sos_abilities[-4:], 0x02B1),
    ("Yuna: Rainbow Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 4, sos_abilities[-4:], 0x02B2),
    ("Auron: Rainbow Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 4, sos_abilities[-4:], 0x02B3),
    ("Kimahri: Rainbow Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 4, sos_abilities[-4:], 0x02B4),
    ("Wakka: Miracle Save",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 4, sos_abilities[-4:], 0x02B5),
    ("Lulu: Rainbow Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 4, sos_abilities[-4:], 0x02B6),
    ("Rikku: Phalanx",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 4, sos_abilities[-4:], 0x02B7),
    ("Seymour: Rainbow Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 4, sos_abilities[-4:], 0x02B8),

    # 4 SOS abilities
    ("Tidus: Shining Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 4, sos_abilities, 0x02B9),
    ("Yuna: Shining Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 4, sos_abilities, 0x02BA),
    ("Auron: Shining Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 4, sos_abilities, 0x02BB),
    ("Kimahri: Shining Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 4, sos_abilities, 0x02BC),
    ("Wakka: Last-Ditch",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 4, sos_abilities, 0x02BD),
    ("Lulu: Shining Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 4, sos_abilities, 0x02BE),
    ("Rikku: Tercio",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 4, sos_abilities, 0x02BF),
    ("Seymour: Shining Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 4, sos_abilities, 0x02C0),

    # 3 status ”proof” abilities
    ("Tidus: Faerie Shield",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 3, status_proofs, 0x02C1),
    ("Yuna: Faerie Ring",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 3, status_proofs, 0x02C2),
    ("Auron: Faerie Bracer",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 3, status_proofs, 0x02C3),
    ("Kimahri: Faerie Armlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 3, status_proofs, 0x02C4),
    ("Wakka: Triple Guard",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 3, status_proofs, 0x02C5),
    ("Lulu: Faerie Bangle",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 3, status_proofs, 0x02C6),
    ("Rikku: Talisman",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 3, status_proofs, 0x02C7),
    ("Seymour: Faerie Circlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 3, status_proofs, 0x02C8),

    # No Encounters
    ("Tidus: Peaceful Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x1D]], 0x02C9),
    ("Yuna: Peaceful Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x1D]], 0x02CA),
    ("Auron: Peaceful Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x1D]], 0x02CB),
    ("Kimahri: Peaceful Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x1D]], 0x02CC),
    ("Wakka: Off-Season",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x1D]], 0x02CD),
    ("Lulu: Peaceful Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x1D]], 0x02CE),
    ("Rikku: Peaceful Targe",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x1D]], 0x02CF),
    ("Seymour: Peaceful Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x1D]], 0x02D0),

    # Auto-Potion
    ("Tidus: Shaman Shield",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x08]], 0x02D1),
    ("Yuna: Shaman Ring",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x08]], 0x02D2),
    ("Auron: Shaman Bracer",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x08]], 0x02D3),
    ("Kimahri: Shaman Armlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x08]], 0x02D4),
    ("Wakka: Shaman Armguard",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x08]], 0x02D5),
    ("Lulu: Shaman Bangle",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x08]], 0x02D6),
    ("Rikku: Shaman Targe",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x08]], 0x02D7),
    ("Seymour: Shaman Circlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x08]], 0x02D8),

    # 3 elemental ”proof” abilities
    ("Tidus: Barrier Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 3, elemental_proofs, 0x02D9),
    ("Yuna: Barrier Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 3, elemental_proofs, 0x02DA),
    ("Auron: Barrier Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 3, elemental_proofs, 0x02DB),
    ("Kimahri: Barrier Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 3, elemental_proofs, 0x02DC),
    ("Wakka: Hat Trick",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 3, elemental_proofs, 0x02DD),
    ("Lulu: Barrier Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 3, elemental_proofs, 0x02DE),
    ("Rikku: Victorious",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 3, elemental_proofs, 0x02DF),
    ("Seymour: Barrier Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 3, elemental_proofs, 0x02E0),

    # 3 SOS abilities
    ("Tidus: Star Shield",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 3, sos_abilities, 0x02E1),
    ("Yuna: Star Ring",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 3, sos_abilities, 0x02E2),
    ("Auron: Star Bracer",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 3, sos_abilities, 0x02E3),
    ("Kimahri: Star Armlet",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 3, sos_abilities, 0x02E4),
    ("Wakka: Pep Talk",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 3, sos_abilities, 0x02E5),
    ("Lulu: Star Bangle",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 3, sos_abilities, 0x02E6),
    ("Rikku: Star Targe",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 3, sos_abilities, 0x02E7),
    ("Seymour: Star Circlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 3, sos_abilities, 0x02E8),

    # 2 ”Auto-” abilities
    ("Tidus: Marching Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 2, auto_abilities, 0x02E9),
    ("Yuna: Marching Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 2, auto_abilities, 0x02EA),
    ("Auron: Marching Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 2, auto_abilities, 0x02EB),
    ("Kimahri: Marching Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 2, auto_abilities, 0x02EC),
    ("Wakka: Auto Armguard",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 2, auto_abilities, 0x02ED),
    ("Lulu: Marching Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 2, auto_abilities, 0x02EE),
    ("Rikku: Marching Targe",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 2, auto_abilities, 0x02EF),
    ("Seymour: Marching Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 2, auto_abilities, 0x02F0),

    # 2 SOS abilities
    ("Tidus: Moon Shield",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 2, sos_abilities, 0x02F1),
    ("Yuna: Moon Ring",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 2, sos_abilities, 0x02F2),
    ("Auron: Moon Bracer",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 2, sos_abilities, 0x02F3),
    ("Kimahri: Moon Armlet",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 2, sos_abilities, 0x02F4),
    ("Wakka: Danger Armguard",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 2, sos_abilities, 0x02F5),
    ("Lulu: Moon Bangle",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 2, sos_abilities, 0x02F6),
    ("Rikku: Moon Targe",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 2, sos_abilities, 0x02F7),
    ("Seymour: Moon Circlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 2, sos_abilities, 0x02F8),

    # Auto-Regen or SOS Regen
    ("Tidus: Regen Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x57], id_to_ability[0x5C]], 0x02F9),
    ("Yuna: Regen Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x57], id_to_ability[0x5C]], 0x02FA),
    ("Auron: Regen Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x57], id_to_ability[0x5C]], 0x02FB),
    ("Kimahri: Regen Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x57], id_to_ability[0x5C]], 0x02FC),
    ("Wakka: Second Wind",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x57], id_to_ability[0x5C]], 0x02FD),
    ("Lulu: Regen Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x57], id_to_ability[0x5C]], 0x02FE),
    ("Rikku: Regen Targe",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x57], id_to_ability[0x5C]], 0x02FF),
    ("Seymour: Regen Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x57], id_to_ability[0x5C]], 0x0300),

    # Auto-Haste or SOS Haste
    ("Tidus: Haste Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x56], id_to_ability[0x5B]], 0x0301),
    ("Yuna: Haste Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x56], id_to_ability[0x5B]], 0x0302),
    ("Auron: Haste Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x56], id_to_ability[0x5B]], 0x0303),
    ("Kimahri: Haste Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x56], id_to_ability[0x5B]], 0x0304),
    ("Wakka: Fast Break",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x56], id_to_ability[0x5B]], 0x0305),
    ("Lulu: Haste Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x56], id_to_ability[0x5B]], 0x0306),
    ("Rikku: Haste Targe",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x56], id_to_ability[0x5B]], 0x0307),
    ("Seymour: Haste Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x56], id_to_ability[0x5B]], 0x0308),

    # Auto-Reflect or SOS Reflect
    ("Tidus: Reflect Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x58], id_to_ability[0x5D]], 0x0309),
    ("Yuna: Reflect Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x58], id_to_ability[0x5D]], 0x030A),
    ("Auron: Reflect Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x58], id_to_ability[0x5D]], 0x030B),
    ("Kimahri: Reflect Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x58], id_to_ability[0x5D]], 0x030C),
    ("Wakka: Reflect Armguard",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x58], id_to_ability[0x5D]], 0x030D),
    ("Lulu: Reflect Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x58], id_to_ability[0x5D]], 0x030E),
    ("Rikku: Reflect Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x58], id_to_ability[0x5D]], 0x030F),
    ("Seymour: Reflect Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x58], id_to_ability[0x5D]], 0x0310),

    # Auto-Shell or SOS Shell
    ("Tidus: Shell Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x54], id_to_ability[0x59]], 0x0311),
    ("Yuna: Shell Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x54], id_to_ability[0x59]], 0x0312),
    ("Auron: Shell Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x54], id_to_ability[0x59]], 0x0313),
    ("Kimahri: Shell Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x54], id_to_ability[0x59]], 0x0314),
    ("Wakka: Shell Armguard",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x54], id_to_ability[0x59]], 0x0315),
    ("Lulu: Shell Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x54], id_to_ability[0x59]], 0x0316),
    ("Rikku: Shell Targe",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x54], id_to_ability[0x59]], 0x0317),
    ("Seymour: Shell Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x54], id_to_ability[0x59]], 0x0318),

    # Auto-Protect or SOS Protect
    ("Tidus: Protect Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x55], id_to_ability[0x5A]], 0x0319),
    ("Yuna: Protect Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x55], id_to_ability[0x5A]], 0x031A),
    ("Auron: Protect Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x55], id_to_ability[0x5A]], 0x031B),
    ("Kimahri: Protect Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x55], id_to_ability[0x5A]], 0x031C),
    ("Wakka: Protect Armguard",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x55], id_to_ability[0x5A]], 0x031D),
    ("Lulu: Protect Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x55], id_to_ability[0x5A]], 0x031E),
    ("Rikku: Protect Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x55], id_to_ability[0x5A]], 0x031F),
    ("Seymour: Protect Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x55], id_to_ability[0x5A]], 0x0320),

    # Alchemy
    ("Tidus: Buckler (Alchemy)",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x07]], 0x0321),
    ("Yuna: Ring (Alchemy)",                   ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x07]], 0x0322),
    ("Auron: Bracer (Alchemy)",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x07]], 0x0323),
    ("Kimahri: Armlet (Alchemy)",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x07]], 0x0324),
    ("Wakka: Armguard (Alchemy)",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x07]], 0x0325),
    ("Lulu: Bangle (Alchemy)",                 ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x07]], 0x0326),
    ("Rikku: Targe (Alchemy)",                 ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x07]], 0x0327),
    ("Seymour: Circlet (Alchemy)",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x07]], 0x0328),

    # 3 Defense +%s
    ("Tidus: Platinum Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 3, defense_abilities, 0x0329),
    ("Yuna: Platinum Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 3, defense_abilities, 0x032A),
    ("Auron: Platinum Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 3, defense_abilities, 0x032B),
    ("Kimahri: Platinum Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 3, defense_abilities, 0x032C),
    ("Wakka: Platinum Armguard",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 3, defense_abilities, 0x032D),
    ("Lulu: Platinum Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 3, defense_abilities, 0x032E),
    ("Rikku: Centurion",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 3, defense_abilities, 0x032F),
    ("Seymour: Platinum Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 3, defense_abilities, 0x0330),

    # 3 Magic Def +%s
    ("Tidus: Sapphire Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 3, magic_defense_abilities, 0x0331),
    ("Yuna: Sapphire Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 3, magic_defense_abilities, 0x0332),
    ("Auron: Sapphire Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 3, magic_defense_abilities, 0x0333),
    ("Kimahri: Sapphire Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 3, magic_defense_abilities, 0x0334),
    ("Wakka: Sapphire Armguard",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 3, magic_defense_abilities, 0x0335),
    ("Lulu: Sapphire Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 3, magic_defense_abilities, 0x0336),
    ("Rikku: Echelon",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 3, magic_defense_abilities, 0x0337),
    ("Seymour: Sapphire Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 3, magic_defense_abilities, 0x0338),

    # 3 HP +%s
    ("Tidus: Knight’s Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 3, hp_abilities, 0x0339),
    ("Yuna: Power Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 3, hp_abilities, 0x033A),
    ("Auron: Knight’s Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 3, hp_abilities, 0x033B),
    ("Kimahri: Knight’s Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 3, hp_abilities, 0x033C),
    ("Wakka: Power Armguard",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 3, hp_abilities, 0x033D),
    ("Lulu: Power Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 3, hp_abilities, 0x033E),
    ("Rikku: Knight’s Targe",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 3, hp_abilities, 0x033F),
    ("Seymour: Power Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 3, hp_abilities, 0x0340),

    # 3 MP +%s
    ("Tidus: Wizard Shield",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 3, mp_abilities, 0x0341),
    ("Yuna: Wizard Ring",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 3, mp_abilities, 0x0342),
    ("Auron: Wizard Bracer",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 3, mp_abilities, 0x0343),
    ("Kimahri: Wizard Armlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 3, mp_abilities, 0x0344),
    ("Wakka: Energy Armguard",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 3, mp_abilities, 0x0345),
    ("Lulu: Wizard Bangle",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 3, mp_abilities, 0x0346),
    ("Rikku: Wizard Targe",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 3, mp_abilities, 0x0347),
    ("Seymour: Wizard Circlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 3, mp_abilities, 0x0348),

    # 2 elemental ”Eater” or ”proof” abilities
    ("Tidus: Elemental Shield",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 2, elemental_eaters+elemental_proofs, 0x0349),
    ("Yuna: Elemental Ring",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 2, elemental_eaters+elemental_proofs, 0x034A),
    ("Auron: Elemental Bracer",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 2, elemental_eaters+elemental_proofs, 0x034B),
    ("Kimahri: Elemental Armlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 2, elemental_eaters+elemental_proofs, 0x034C),
    ("Wakka: Elemental Armguard",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 2, elemental_eaters+elemental_proofs, 0x034D),
    ("Lulu: Elemental Bangle",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 2, elemental_eaters+elemental_proofs, 0x034E),
    ("Rikku: Elemental Targe",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 2, elemental_eaters+elemental_proofs, 0x034F),
    ("Seymour: Elemental Circlet",   ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 2, elemental_eaters+elemental_proofs, 0x0350),

    # 2 status ”proof” abilities
    ("Tidus: Defending Shield",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 2, status_proofs, 0x0351),
    ("Yuna: Defending Ring",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 2, status_proofs, 0x0352),
    ("Auron: Defending Bracer",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 2, status_proofs, 0x0353),
    ("Kimahri: Defending Armlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 2, status_proofs, 0x0354),
    ("Wakka: Low Risk",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 2, status_proofs, 0x0355),
    ("Lulu: Savior Bangle",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 2, status_proofs, 0x0356),
    ("Rikku: Reliant",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 2, status_proofs, 0x0357),
    ("Seymour: Savior Circlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 2, status_proofs, 0x0358),

    # Fire Eater
    ("Tidus: Crimson Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x21]], 0x0359),
    ("Yuna: Crimson Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x21]], 0x035A),
    ("Auron: Crimson Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x21]], 0x035B),
    ("Kimahri: Crimson Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x21]], 0x035C),
    ("Wakka: Crimson Armguard",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x21]], 0x035D),
    ("Lulu: Crimson Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x21]], 0x035E),
    ("Rikku: Crimson Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x21]], 0x035F),
    ("Seymour: Crimson Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x21]], 0x0360),

    # Ice Eater
    ("Tidus: Snow Shield",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x25]], 0x0361),
    ("Yuna: Snow Ring",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x25]], 0x0362),
    ("Auron: Snow Bracer",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x25]], 0x0363),
    ("Kimahri: Snow Armlet",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x25]], 0x0364),
    ("Wakka: Snow Armguard",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x25]], 0x0365),
    ("Lulu: Snow Bangle",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x25]], 0x0366),
    ("Rikku: Snow Targe",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x25]], 0x0367),
    ("Seymour: Snow Circlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x25]], 0x0368),

    # Lightning Eater
    ("Tidus: Ochre Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x29]], 0x0369),
    ("Yuna: Ochre Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x29]], 0x036A),
    ("Auron: Ochre Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x29]], 0x036B),
    ("Kimahri: Ochre Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x29]], 0x036C),
    ("Wakka: Ochre Armguard",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x29]], 0x036D),
    ("Lulu: Ochre Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x29]], 0x036E),
    ("Rikku: Ochre Targe",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x29]], 0x036F),
    ("Seymour: Ochre Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x29]], 0x0370),

    # Water Eater
    ("Tidus: Cerulean Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x2D]], 0x0371),
    ("Yuna: Cerulean Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x2D]], 0x0372),
    ("Auron: Cerulean Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x2D]], 0x0373),
    ("Kimahri: Cerulean Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x2D]], 0x0374),
    ("Wakka: Cerulean Armguard",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x2D]], 0x0375),
    ("Lulu: Cerulean Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x2D]], 0x0376),
    ("Rikku: Cerulean Targe",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x2D]], 0x0377),
    ("Seymour: Cerulean Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x2D]], 0x0378),

    # Curseproof or Curse Ward (Ward is invalid)
    ("Tidus: Medical Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x52]], 0x0379),
    ("Yuna: Medical Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x52]], 0x037A),
    ("Auron: Medical Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x52]], 0x037B),
    ("Kimahri: Medical Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x52]], 0x037C),
    ("Wakka: Medical Armguard",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x52]], 0x037D),
    ("Lulu: Medical Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x52]], 0x037E),
    ("Rikku: Medical Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x52]], 0x037F),
    ("Seymour: Medical Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x52]], 0x0380),

    # Confuseproof or Confuse Ward
    ("Tidus: Lucid Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x4E], id_to_ability[0x4F]], 0x0381),
    ("Yuna: Lucid Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x4E], id_to_ability[0x4F]], 0x0382),
    ("Auron: Lucid Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x4E], id_to_ability[0x4F]], 0x0383),
    ("Kimahri: Lucid Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x4E], id_to_ability[0x4F]], 0x0384),
    ("Wakka: Lucid Armguard",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x4E], id_to_ability[0x4F]], 0x0385),
    ("Lulu: Lucid Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x4E], id_to_ability[0x4F]], 0x0386),
    ("Rikku: Lucid Targe",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x4E], id_to_ability[0x4F]], 0x0387),
    ("Seymour: Lucid Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x4E], id_to_ability[0x4F]], 0x0388),

    # Berserkproof or Berserk Ward
    ("Tidus: Serene Shield",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x50], id_to_ability[0x51]], 0x0389),
    ("Yuna: Serene Ring",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x50], id_to_ability[0x51]], 0x038A),
    ("Auron: Serene Bracer",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x50], id_to_ability[0x51]], 0x038B),
    ("Kimahri: Serene Armlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x50], id_to_ability[0x51]], 0x038C),
    ("Wakka: Serene Armguard",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x50], id_to_ability[0x51]], 0x038D),
    ("Lulu: Serene Bangle",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x50], id_to_ability[0x51]], 0x038E),
    ("Rikku: Dauntless",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x50], id_to_ability[0x51]], 0x038F),
    ("Seymour: Serene Circlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x50], id_to_ability[0x51]], 0x0390),

    # Slowproof or Slow Ward
    ("Tidus: Light Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x4C], id_to_ability[0x4D]], 0x0391),
    ("Yuna: Light Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x4C], id_to_ability[0x4D]], 0x0392),
    ("Auron: Light Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x4C], id_to_ability[0x4D]], 0x0393),
    ("Kimahri: Light Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x4C], id_to_ability[0x4D]], 0x0394),
    ("Wakka: Light Armguard",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x4C], id_to_ability[0x4D]], 0x0395),
    ("Lulu: Light Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x4C], id_to_ability[0x4D]], 0x0396),
    ("Rikku: Light Targe",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x4C], id_to_ability[0x4D]], 0x0397),
    ("Seymour: Light Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x4C], id_to_ability[0x4D]], 0x0398),

    # Deathproof or Death Ward
    ("Tidus: Soul Shield",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x30], id_to_ability[0x31]], 0x0399),
    ("Yuna: Soul Ring",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x30], id_to_ability[0x31]], 0x039A),
    ("Auron: Soul Bracer",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x30], id_to_ability[0x31]], 0x039B),
    ("Kimahri: Soul Armlet",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x30], id_to_ability[0x31]], 0x039C),
    ("Wakka: Soul Armguard",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x30], id_to_ability[0x31]], 0x039D),
    ("Lulu: Soul Bangle",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x30], id_to_ability[0x31]], 0x039E),
    ("Rikku: Soul Targe",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x30], id_to_ability[0x31]], 0x039F),
    ("Seymour: Soul Circlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x30], id_to_ability[0x31]], 0x03A0),

    # Zombieproof or Zombie Ward
    ("Tidus: Blessed Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x34], id_to_ability[0x35]], 0x03A1),
    ("Yuna: Blessed Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x34], id_to_ability[0x35]], 0x03A2),
    ("Auron: Blessed Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x34], id_to_ability[0x35]], 0x03A3),
    ("Kimahri: Blessed Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x34], id_to_ability[0x35]], 0x03A4),
    ("Wakka: Blessed Armguard",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x34], id_to_ability[0x35]], 0x03A5),
    ("Lulu: Blessed Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x34], id_to_ability[0x35]], 0x03A6),
    ("Rikku: Blessed Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x34], id_to_ability[0x35]], 0x03A7),
    ("Seymour: Blessed Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x34], id_to_ability[0x35]], 0x03A8),

    # Stoneproof or Stone Ward
    ("Tidus: Soft Shield",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x38], id_to_ability[0x39]], 0x03A9),
    ("Yuna: Soft Ring",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x38], id_to_ability[0x39]], 0x03AA),
    ("Auron: Soft Bracer",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x38], id_to_ability[0x39]], 0x03AB),
    ("Kimahri: Soft Armlet",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x38], id_to_ability[0x39]], 0x03AC),
    ("Wakka: Soft Armguard",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x38], id_to_ability[0x39]], 0x03AD),
    ("Lulu: Soft Bangle",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x38], id_to_ability[0x39]], 0x03AE),
    ("Rikku: Soft Targe",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x38], id_to_ability[0x39]], 0x03AF),
    ("Seymour: Soft Circlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x38], id_to_ability[0x39]], 0x03B0),

    # Poisonproof or Poison Ward
    ("Tidus: Serum Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x3C], id_to_ability[0x3D]], 0x03B1),
    ("Yuna: Serum Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x3C], id_to_ability[0x3D]], 0x03B2),
    ("Auron: Serum Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x3C], id_to_ability[0x3D]], 0x03B3),
    ("Kimahri: Serum Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x3C], id_to_ability[0x3D]], 0x03B4),
    ("Wakka: Serum Armguard",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x3C], id_to_ability[0x3D]], 0x03B5),
    ("Lulu: Serum Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x3C], id_to_ability[0x3D]], 0x03B6),
    ("Rikku: Serum Targe",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x3C], id_to_ability[0x3D]], 0x03B7),
    ("Seymour: Serum Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x3C], id_to_ability[0x3D]], 0x03B8),

    # Sleepproof or Sleep Ward
    ("Tidus: Alert Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x40], id_to_ability[0x41]], 0x03B9),
    ("Yuna: Alert Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x40], id_to_ability[0x41]], 0x03BA),
    ("Auron: Alert Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x40], id_to_ability[0x41]], 0x03BB),
    ("Kimahri: Alert Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x40], id_to_ability[0x41]], 0x03BC),
    ("Wakka: Alert Armguard",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x40], id_to_ability[0x41]], 0x03BD),
    ("Lulu: Alert Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x40], id_to_ability[0x41]], 0x03BE),
    ("Rikku: Alert Targe",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x40], id_to_ability[0x41]], 0x03BF),
    ("Seymour: Alert Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x40], id_to_ability[0x41]], 0x03C0),

    # Silenceproof or Silence Ward
    ("Tidus: Echo Shield",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x44], id_to_ability[0x45]], 0x03C1),
    ("Yuna: Echo Ring",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x44], id_to_ability[0x45]], 0x03C2),
    ("Auron: Echo Bracer",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x44], id_to_ability[0x45]], 0x03C3),
    ("Kimahri: Echo Armlet",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x44], id_to_ability[0x45]], 0x03C4),
    ("Wakka: Echo Armguard",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x44], id_to_ability[0x45]], 0x03C5),
    ("Lulu: Echo Bangle",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x44], id_to_ability[0x45]], 0x03C6),
    ("Rikku: Echo Targe",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x44], id_to_ability[0x45]], 0x03C7),
    ("Seymour: Echo Circlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x44], id_to_ability[0x45]], 0x03C8),

    # Darkproof or Dark Ward
    ("Tidus: Bright Shield",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x48], id_to_ability[0x49]], 0x03C9),
    ("Yuna: Bright Ring",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x48], id_to_ability[0x49]], 0x03CA),
    ("Auron: Bright Bracer",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x48], id_to_ability[0x49]], 0x03CB),
    ("Kimahri: Bright Armlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x48], id_to_ability[0x49]], 0x03CC),
    ("Wakka: Bright Armguard",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x48], id_to_ability[0x49]], 0x03CD),
    ("Lulu: Bright Bangle",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x48], id_to_ability[0x49]], 0x03CE),
    ("Rikku: Bright Targe",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x48], id_to_ability[0x49]], 0x03CF),
    ("Seymour: Bright Circlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x48], id_to_ability[0x49]], 0x03D0),

    # Fireproof or Fire Ward
    ("Tidus: Red Shield",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x20], id_to_ability[0x1F]], 0x03D1),
    ("Yuna: Red Ring",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x20], id_to_ability[0x1F]], 0x03D2),
    ("Auron: Red Bracer",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x20], id_to_ability[0x1F]], 0x03D3),
    ("Kimahri: Red Armlet",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x20], id_to_ability[0x1F]], 0x03D4),
    ("Wakka: Red Armguard",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x20], id_to_ability[0x1F]], 0x03D5),
    ("Lulu: Red Bangle",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x20], id_to_ability[0x1F]], 0x03D6),
    ("Rikku: Red Targe",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x20], id_to_ability[0x1F]], 0x03D7),
    ("Seymour: Red Circlet",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x20], id_to_ability[0x1F]], 0x03D8),

    # Iceproof or Ice Ward
    ("Tidus: White Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x24], id_to_ability[0x23]], 0x03D9),
    ("Yuna: White Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x24], id_to_ability[0x23]], 0x03DA),
    ("Auron: White Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x24], id_to_ability[0x23]], 0x03DB),
    ("Kimahri: White Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x24], id_to_ability[0x23]], 0x03DC),
    ("Wakka: White Armguard",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x24], id_to_ability[0x23]], 0x03DD),
    ("Lulu: White Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x24], id_to_ability[0x23]], 0x03DE),
    ("Rikku: White Targe",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x24], id_to_ability[0x23]], 0x03DF),
    ("Seymour: White Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x24], id_to_ability[0x23]], 0x03E0),

    # Lightningproof or Lightning Ward
    ("Tidus: Yellow Shield",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x28], id_to_ability[0x27]], 0x03E1),
    ("Yuna: Yellow Ring",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x28], id_to_ability[0x27]], 0x03E2),
    ("Auron: Yellow Bracer",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x28], id_to_ability[0x27]], 0x03E3),
    ("Kimahri: Yellow Armlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x28], id_to_ability[0x27]], 0x03E4),
    ("Wakka: Yellow Armguard",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x28], id_to_ability[0x27]], 0x03E5),
    ("Lulu: Yellow Bangle",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x28], id_to_ability[0x27]], 0x03E6),
    ("Rikku: Yellow Targe",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x28], id_to_ability[0x27]], 0x03E7),
    ("Seymour: Yellow Circlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x28], id_to_ability[0x27]], 0x03E8),

    # Waterproof or Water Ward
    ("Tidus: Blue Shield",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x2C], id_to_ability[0x2B]], 0x03E9),
    ("Yuna: Blue Ring",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x2C], id_to_ability[0x2B]], 0x03EA),
    ("Auron: Blue Bracer",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x2C], id_to_ability[0x2B]], 0x03EB),
    ("Kimahri: Blue Armlet",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x2C], id_to_ability[0x2B]], 0x03EC),
    ("Wakka: Blue Armguard",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x2C], id_to_ability[0x2B]], 0x03ED),
    ("Lulu: Blue Bangle",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x2C], id_to_ability[0x2B]], 0x03EE),
    ("Rikku: Blue Targe",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x2C], id_to_ability[0x2B]], 0x03EF),
    ("Seymour: Blue Circlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x2C], id_to_ability[0x2B]], 0x03F0),

    # SOS NulTide
    ("Tidus: NulTide Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x5E]], 0x03F1),
    ("Yuna: NulTide Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x5E]], 0x03F2),
    ("Auron: NulTide Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x5E]], 0x03F3),
    ("Kimahri: NulTide Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x5E]], 0x03F4),
    ("Wakka: NulTide Armguard",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x5E]], 0x03F5),
    ("Lulu: NulTide Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x5E]], 0x03F6),
    ("Rikku: NulTide Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x5E]], 0x03F7),
    ("Seymour: NulTide Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x5E]], 0x03F8),

    # SOS NulBlaze
    ("Tidus: NulBlaze Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x61]], 0x03F9),
    ("Yuna: NulBlaze Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x61]], 0x03FA),
    ("Auron: NulBlaze Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x61]], 0x03FB),
    ("Kimahri: NulBlaze Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x61]], 0x03FC),
    ("Wakka: NulBlaze Armguard",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x61]], 0x03FD),
    ("Lulu: NulBlaze Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x61]], 0x03FE),
    ("Rikku: NulBlaze Targe",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x61]], 0x03FF),
    ("Seymour: NulBlaze Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x61]], 0x0400),

    # SOS NulShock
    ("Tidus: NulShock Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x60]], 0x0401),
    ("Yuna: NulShock Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x60]], 0x0402),
    ("Auron: NulShock Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x60]], 0x0403),
    ("Kimahri: NulShock Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x60]], 0x0404),
    ("Wakka: NulShock Armguard",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x60]], 0x0405),
    ("Lulu: NulShock Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x60]], 0x0406),
    ("Rikku: NulShock Targe",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x60]], 0x0407),
    ("Seymour: NulShock Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x60]], 0x0408),

    # SOS NulFrost
    ("Tidus: NulFrost Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, [id_to_ability[0x5F]], 0x0409),
    ("Yuna: NulFrost Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, [id_to_ability[0x5F]], 0x040A),
    ("Auron: NulFrost Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, [id_to_ability[0x5F]], 0x040B),
    ("Kimahri: NulFrost Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, [id_to_ability[0x5F]], 0x040C),
    ("Wakka: NulFrost Armguard",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, [id_to_ability[0x5F]], 0x040D),
    ("Lulu: NulFrost Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, [id_to_ability[0x5F]], 0x040E),
    ("Rikku: NulFrost Targe",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, [id_to_ability[0x5F]], 0x040F),
    ("Seymour: NulFrost Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, [id_to_ability[0x5F]], 0x0410),

    # 4 HP or MP +%s
    ("Tidus: Adept’s Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 4, hp_abilities+mp_abilities, 0x0411),
    ("Yuna: Adept’s Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 4, hp_abilities+mp_abilities, 0x0412),
    ("Auron: Adept’s Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 4, hp_abilities+mp_abilities, 0x0413),
    ("Kimahri: Adept’s Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 4, hp_abilities+mp_abilities, 0x0414),
    ("Wakka: Adept’s Armguard",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 4, hp_abilities+mp_abilities, 0x0415),
    ("Lulu: Adept’s Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 4, hp_abilities+mp_abilities, 0x0416),
    ("Rikku: Adept’s Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 4, hp_abilities+mp_abilities, 0x0417),
    ("Seymour: Adept's Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 4, hp_abilities+mp_abilities, 0x0418),

    # 4 slots
    ("Tidus: Tetra Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 4, [], 0x0419),
    ("Yuna: Tetra Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 4, [], 0x041A),
    ("Auron: Tetra Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 4, [], 0x041B),
    ("Kimahri: Tetra Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 4, [], 0x041C),
    ("Wakka: Tetra Armguard",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 4, [], 0x041D),
    ("Lulu: Tetra Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 4, [], 0x041E),
    ("Rikku: Tetra Targe",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 4, [], 0x041F),
    ("Seymour: Tetra Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 4, [], 0x0420),

    # 1 Defense +%s and at least 1 Magic Def +%s
    ("Tidus: Mythril Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 2, [defense_abilities, magic_defense_abilities], 0x0421),
    ("Yuna: Mythril Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 2, [defense_abilities, magic_defense_abilities], 0x0422),
    ("Auron: Mythril Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 2, [defense_abilities, magic_defense_abilities], 0x0423),
    ("Kimahri: Mythril Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 2, [defense_abilities, magic_defense_abilities], 0x0424),
    ("Wakka: Mythril Armguard",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 2, [defense_abilities, magic_defense_abilities], 0x0425),
    ("Lulu: Mythril Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 2, [defense_abilities, magic_defense_abilities], 0x0426),
    ("Rikku: Mythril Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 2, [defense_abilities, magic_defense_abilities], 0x0427),
    ("Seymour: Mythril Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 2, [defense_abilities, magic_defense_abilities], 0x0428),

    # 2 Defense +%s
    ("Tidus: Gold Shield",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 2, defense_abilities, 0x0429),
    ("Yuna: Gold Ring",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 2, defense_abilities, 0x042A),
    ("Auron: Gold Bracer",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 2, defense_abilities, 0x042B),
    ("Kimahri: Gold Armlet",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 2, defense_abilities, 0x042C),
    ("Wakka: Gold Armguard",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 2, defense_abilities, 0x042D),
    ("Lulu: Gold Bangle",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 2, defense_abilities, 0x042E),
    ("Rikku: Gold Targe",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 2, defense_abilities, 0x042F),
    ("Seymour: Gold Circlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 2, defense_abilities, 0x0430),

    # 2 Magic Def +%s
    ("Tidus: Emerald Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 2, magic_defense_abilities, 0x0431),
    ("Yuna: Emerald Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 2, magic_defense_abilities, 0x0432),
    ("Auron: Emerald Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 2, magic_defense_abilities, 0x0433),
    ("Kimahri: Emerald Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 2, magic_defense_abilities, 0x0434),
    ("Wakka: Emerald Armguard",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 2, magic_defense_abilities, 0x0435),
    ("Lulu: Emerald Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 2, magic_defense_abilities, 0x0436),
    ("Rikku: Emerald Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 2, magic_defense_abilities, 0x0437),
    ("Seymour: Emerald Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 2, magic_defense_abilities, 0x0438),

    # 2 HP +%s
    ("Tidus: Soldier’s Shield",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 2, hp_abilities, 0x0439),
    ("Yuna: Soldier’s Ring",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 2, hp_abilities, 0x043A),
    ("Auron: Soldier’s Bracer",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 2, hp_abilities, 0x043B),
    ("Kimahri: Soldier’s Armlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 2, hp_abilities, 0x043C),
    ("Wakka: Soldier’s Armguard",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 2, hp_abilities, 0x043D),
    ("Lulu: Vita Bangle",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 2, hp_abilities, 0x043E),
    ("Rikku: Soldier’s Targe",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 2, hp_abilities, 0x043F),
    ("Seymour: Vita Circlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 2, hp_abilities, 0x0440),

    # 2 MP +%s
    ("Tidus: Mage’s Shield",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 2, mp_abilities, 0x0441),
    ("Yuna: Mage’s Ring",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 2, mp_abilities, 0x0442),
    ("Auron: Mage’s Bracer",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 2, mp_abilities, 0x0443),
    ("Kimahri: Mage’s Armlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 2, mp_abilities, 0x0444),
    ("Wakka: Mage’s Armguard",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 2, mp_abilities, 0x0445),
    ("Lulu: Mage’s Bangle",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 2, mp_abilities, 0x0446),
    ("Rikku: Mage’s Targe",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 2, mp_abilities, 0x0447),
    ("Seymour: Mage's Circlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 2, mp_abilities, 0x0448),

    # Defense +10% or Defense +20%
    ("Tidus: Silver Shield",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, defense_abilities[2:], 0x0449),
    ("Yuna: Silver Ring",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, defense_abilities[2:], 0x044A),
    ("Auron: Silver Bracer",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, defense_abilities[2:], 0x044B),
    ("Kimahri: Silver Armlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, defense_abilities[2:], 0x044C),
    ("Wakka: Silver Armguard",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, defense_abilities[2:], 0x044D),
    ("Lulu: Silver Bangle",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, defense_abilities[2:], 0x044E),
    ("Rikku: Silver Targe",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, defense_abilities[2:], 0x044F),
    ("Seymour: Silver Circlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, defense_abilities[2:], 0x0450),

    # Magic Def +10% or Magic Def +20%
    ("Tidus: Onyx Shield",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, magic_defense_abilities[2:], 0x0451),
    ("Yuna: Onyx Ring",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, magic_defense_abilities[2:], 0x0452),
    ("Auron: Onyx Bracer",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, magic_defense_abilities[2:], 0x0453),
    ("Kimahri: Onyx Armlet",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, magic_defense_abilities[2:], 0x0454),
    ("Wakka: Onyx Armguard",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, magic_defense_abilities[2:], 0x0455),
    ("Lulu: Onyx Bangle",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, magic_defense_abilities[2:], 0x0456),
    ("Rikku: Onyx Targe",            ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, magic_defense_abilities[2:], 0x0457),
    ("Seymour: Onyx Circlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, magic_defense_abilities[2:], 0x0458),

    # MP +20% or MP +30%
    ("Tidus: Sorcery Shield",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, mp_abilities[2:], 0x0459),
    ("Yuna: Sorcery Ring",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, mp_abilities[2:], 0x045A),
    ("Auron: Sorcery Bracer",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, mp_abilities[2:], 0x045B),
    ("Kimahri: Sorcery Armlet",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, mp_abilities[2:], 0x045C),
    ("Wakka: Sorcery Armguard",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, mp_abilities[2:], 0x045D),
    ("Lulu: Sorcery Bangle",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, mp_abilities[2:], 0x045E),
    ("Rikku: Sorcery Targe",         ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, mp_abilities[2:], 0x045F),
    ("Seymour: Sorcery Circlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, mp_abilities[2:], 0x0460),

    # HP +20% or HP +30%
    ("Tidus: Warrior’s Shield",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, hp_abilities[2:], 0x0461),
    ("Yuna: Tough Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, hp_abilities[2:], 0x0462),
    ("Auron: Warrior’s Bracer",      ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, hp_abilities[2:], 0x0463),
    ("Kimahri: Warrior’s Armlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, hp_abilities[2:], 0x0464),
    ("Wakka: Warrior’s Armguard",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, hp_abilities[2:], 0x0465),
    ("Lulu: Tough Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, hp_abilities[2:], 0x0466),
    ("Rikku: Warrior’s Targe",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, hp_abilities[2:], 0x0467),
    ("Seymour: Tough Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, hp_abilities[2:], 0x0468),

    # 3 slots
    ("Tidus: Glorious Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 3, [], 0x0469),
    ("Yuna: Glorious Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 3, [], 0x046A),
    ("Auron: Glorious Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 3, [], 0x046B),
    ("Kimahri: Glorious Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 3, [], 0x046C),
    ("Wakka: Glorious Armguard",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 3, [], 0x046D),
    ("Lulu: Glorious Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 3, [], 0x046E),
    ("Rikku: Glorious Targe",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 3, [], 0x046F),
    ("Seymour: Glorious Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 3, [], 0x0470),

    # Defense +3% or Defense +5%
    ("Tidus: Metal Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, defense_abilities[:2], 0x0471),
    ("Yuna: Metal Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, defense_abilities[:2], 0x0472),
    ("Auron: Metal Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, defense_abilities[:2], 0x0473),
    ("Kimahri: Metal Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, defense_abilities[:2], 0x0474),
    ("Wakka: Metal Armguard",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, defense_abilities[:2], 0x0475),
    ("Lulu: Metal Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, defense_abilities[:2], 0x0476),
    ("Rikku: Metal Targe",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, defense_abilities[:2], 0x0477),
    ("Seymour: Metal Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, defense_abilities[:2], 0x0478),

    # Magic Def +3% or Magic Def +5%
    ("Tidus: Pearl Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, magic_defense_abilities[:2], 0x0479),
    ("Yuna: Pearl Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, magic_defense_abilities[:2], 0x047A),
    ("Auron: Pearl Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, magic_defense_abilities[:2], 0x047B),
    ("Kimahri: Pearl Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, magic_defense_abilities[:2], 0x047C),
    ("Wakka: Pearl Armguard",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, magic_defense_abilities[:2], 0x047D),
    ("Lulu: Pearl Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, magic_defense_abilities[:2], 0x047E),
    ("Rikku: Pearl Targe",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, magic_defense_abilities[:2], 0x047F),
    ("Seymour: Pearl Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, magic_defense_abilities[:2], 0x0480),

    # MP +5% or MP +10%
    ("Tidus: Magic Shield",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, mp_abilities[:2], 0x0481),
    ("Yuna: Magic Ring",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, mp_abilities[:2], 0x0482),
    ("Auron: Magic Bracer",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, mp_abilities[:2], 0x0483),
    ("Kimahri: Magic Armlet",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, mp_abilities[:2], 0x0484),
    ("Wakka: Magic Armguard",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, mp_abilities[:2], 0x0485),
    ("Lulu: Magic Bangle",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, mp_abilities[:2], 0x0486),
    ("Rikku: Magic Targe",           ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, mp_abilities[:2], 0x0487),
    ("Seymour: Magic Circlet",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, mp_abilities[:2], 0x0488),

    # HP +5% or HP +10%
    ("Tidus: Seeker’s Shield",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 1, hp_abilities[:2], 0x0489),
    ("Yuna: Seeker’s Ring",          ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 1, hp_abilities[:2], 0x048A),
    ("Auron: Seeker’s Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 1, hp_abilities[:2], 0x048B),
    ("Kimahri: Seeker’s Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 1, hp_abilities[:2], 0x048C),
    ("Wakka: Seeker’s Armguard",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 1, hp_abilities[:2], 0x048D),
    ("Lulu: Seeker’s Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 1, hp_abilities[:2], 0x048E),
    ("Rikku: Seeker’s Targe",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 1, hp_abilities[:2], 0x048F),
    ("Seymour: Seeker's Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 1, hp_abilities[:2], 0x0490),

    # 2 slots
    ("Tidus: Shield",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 2, [], 0x0491),
    ("Yuna: Wide Ring",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 2, [], 0x0492),
    ("Auron: Guardian Bracer",       ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 2, [], 0x0493),
    ("Kimahri: Guardian Armlet",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 2, [], 0x0494),
    ("Wakka: Guardian Armguard",     ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 2, [], 0x0495),
    ("Lulu: Guardian Bangle",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 2, [], 0x0496),
    ("Rikku: Guardian Targe",        ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 2, [], 0x0497),
    ("Seymour: Guardian Circlet",    ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 2, [], 0x0498),

    # Else
    ("Tidus: Buckler",               ItemClassification.useful     , GearFlag.NONE       , PlySaveId.TIDUS  , GearType.ARMOR , 0, [], 0x0499),
    ("Yuna: Ring",                   ItemClassification.useful     , GearFlag.NONE       , PlySaveId.YUNA   , GearType.ARMOR , 0, [], 0x049A),
    ("Auron: Bracer",                ItemClassification.useful     , GearFlag.NONE       , PlySaveId.AURON  , GearType.ARMOR , 0, [], 0x049B),
    ("Kimahri: Armlet",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.KIMAHRI, GearType.ARMOR , 0, [], 0x049C),
    ("Wakka: Armguard",              ItemClassification.useful     , GearFlag.NONE       , PlySaveId.WAKKA  , GearType.ARMOR , 0, [], 0x049D),
    ("Lulu: Bangle",                 ItemClassification.useful     , GearFlag.NONE       , PlySaveId.LULU   , GearType.ARMOR , 0, [], 0x049E),
    ("Rikku: Targe",                 ItemClassification.useful     , GearFlag.NONE       , PlySaveId.RIKKU  , GearType.ARMOR , 0, [], 0x049F),
    ("Seymour: Circlet",             ItemClassification.useful     , GearFlag.NONE       , PlySaveId.SEYMOUR, GearType.ARMOR , 0, [], 0x04A0),
]]
