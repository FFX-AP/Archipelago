from dataclasses import dataclass
from itertools import combinations
from BaseClasses import Entrance, Region
from rule_builder.rules import Has, HasAll
from .locations import FFXSphereGridLocations

class SphereGridNode:
    idx: int
    type_: int
    connections: list[SphereGridNode]
    region: Region

class SphereGridLink:
    node_a_idx: int
    node_b_idx: int


def parse_grid(layout_filepath: str, types_filepath: str) -> list[SphereGridNode]:
    HEADER_SIZE = 0x10
    CLUSTER_SIZE = 0x10
    NODE_SIZE = 0xC
    LINK_SIZE = 0x8

    TYPES_HEADER_SIZE = 0x8

    with (
        open(layout_filepath, mode="rb") as grid_file,
        open(types_filepath, mode="rb") as types_file
    ):
        grid = grid_file.read()
        types = types_file.read()

        cluster_count = struct.unpack("<H", grid[2:4])
        node_count = struct.unpack("<H", grid[4:6])
        link_count = struct.unpack("<H", grid[6:8])

        types_node_count = struct.unpack("<H", types[2:4])

        if node_count != types_node_count:
            raise Exception("Layout file's node count did not match types file's node count.")

        nodes = [SphereGridNode()] * node_count
        links = [SphereGridLink()] * link_count

        # Skip clusters (to nodes)
        grid = grid[(HEADER_SIZE + cluster_count * CLUSTER_SIZE):]

        for node_idx in range(0, node_count):
            node = nodes[node_idx]

            node.idx = node_idx
            node.type_ = struct.unpack("B", types[TYPE_HEADER_SIZE + node_idx])
            node.connections = []

        # Skip nodes (to links)
        grid = grid[(node_count * NODE_SIZE):]

        for link_idx in range(0, link_count):
            link = links[link_idx]

            link_offset = link_idx * LINK_SIZE
            link_data = grid[link_offset:(link_offset + LINK_SIZE)]

            link.node_a_idx = struct.unpack("<H", link_data[0:2])
            link.node_b_idx = struct.unpack("<H", link_data[2:4])
            
            # Connect the nodes
            nodes[link.node_a_idx].connections.append(nodes[link.node_b_idx])
            nodes[link.node_b_idx].connections.append(nodes[link.node_a_idx])

        return nodes


def node_get_lock_level(node: SphereGridNode) -> int:
    match node.type_:
        case 0x27: return 1
        case 0x28: return 2
        case 0x00: return 3
        case 0x29: return 4
    return 0


def node_is_lock(node: SphereGridNode) -> bool:
    return node_get_lock_level(node) != 0


def node_is_ability(node: SphereGridNode) -> bool:
    return node.type_ >= 0x2A and node.type_ <= 0x7E


#TODO: Look into replacing this with an iterative queue-based exploration
def explore_node(explored: list[int], node: SphereGridNode) -> None:
    for other_node in node.connections:
        if other_node.idx in explored:
            continue
        
        if node_is_lock(other_node):
            continue
        
        explored.append(other_node.idx)
        explore_node(explored, other_node)


#TODO: Look into replacing this with an iterative queue-based exploration
def explore_lock_chain(
    explored: list[int],
    lock_levels_stack: list[int],
    connecting_regions: dict[Region, list[set[int]]],
    node: SphereGridNode
) -> None:
    for other_node in node.connections:
        if other_node.idx in explored:
            continue
        
        if not node_is_lock(other_node):
            if other_node.region not in connecting_regions.keys():
                connecting_regions[other_node.region] = []

            current_path = set(lock_levels_stack)

            found_same = False
            for path in connecting_regions[other_node.region]:
                if len(current_path.symmetric_difference(path)) == 0:
                    found_same = True
                
            if not found_same:
                connecting_regions[other_node.region].append(current_path)
            continue

        lock_level = node_get_lock_level(other_node)

        explored.append(other_node.idx)
        lock_levels_stack.append(lock_level)
        explore_lock_chain(explored, lock_levels_stack, connecting_region, other_node)
    
    lock_levels_stack.pop()


def get_rule_for_locks(lock_levels: set[int]) -> Rule[FFXWorld]:
    required_items: list[str] = []

    for lock_level in lock_levels:
        required_items.append(f"Sphere Grid: Unlock All Lv. {lock_level} Locks")
    
    if len(required_items) == 1:
        return Has(required_items[0])
    
    return HasAll(*required_items)


def split_nodes_into_regions(world: FFXWorld, nodes: list[SphereGridNode]) -> None:
    locks: list[SphereGridNode] = []

    region_count: int = 0

    # Explore all nodes and flood-fill them with regions, using locks as boundaries
    for node in nodes:
        if node_is_lock(node):
            locks.append(node)
            continue
        
        if node.region == None:
            region_nodes: list[SphereGridNode] = [ node ]
            explore_node(region_nodes, node)

            region_count += 1
            region: Region = Region(f"Sphere Grid Region #{region_count}", world.player, world.multiworld)

            for region_node in region_nodes:
                region_node.region = region

                if node_is_ability(region_node):
                    location_data: FFXLocationData = FFXSphereGridLocations[region_node.type_ - 0x2A]
                    new_location: FFXLocation = FFXLocation(world.player, location_data.name, location_data.rom_address, region)
                    region.locations.append(new_location)

    # All nodes, except locks, are guaranteed to have regions assigned now
    for lock in locks:
        lock_level = node_get_lock_level(lock)

        from_regions: list[Region] = []

        for other_node in lock.connections:
            if node_is_lock(other_node):
                continue

            if other_node.region not in from_regions:
                from_regions.append(other_node.region)
        
        lock_chain: list[SphereGridNode] = [ lock ]
        lock_levels_stack: list[int] = [ lock_level ]
        lock_chain_connecting_regions: dict[Region, list[set[int]]] = { }

        if len(from_regions) > 1:
            for region in from_regions:
                lock_chain_connecting_regions[region] = [ lock_levels_stack.copy() ]
        
        for other_node in lock.connections:
            if not node_is_lock(other_node):
                continue

            explore_lock_chain(lock_chain, lock_levels_stack, lock_chain_connecting_regions, other_node)
        
        for to_region in lock_chain_connecting_regions.keys():
            for from_region in from_regions:
                if to_region == from_region:
                    continue

                lock_chain_rule: Rule[FFXWorld] = get_rule_for_locks(lock_chain_connecting_regions[to_region])
                from_region.connect(to_region, rule=lock_chain_rule)


