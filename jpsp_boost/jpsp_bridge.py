from model import Coordinate
from jpsp_c_api import libjpsp


def xy_to_loc(x, y):
    return libjpsp.XYLoc(int(x), int(y))


def make_map_data(map_width, map_height, buildings, search_height):
    map_data = libjpsp.VecBool()

    for _ in range(map_width * map_height):
        map_data.append(True)

    for building in buildings:
        x1, y1, x2, y2, z1, z2 = building

        if z1 <= search_height <= z2:
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    map_data[x + y * map_width] = False

    return map_data


def loc_path_to_coordinate_path(path: [libjpsp.XYLoc], height) -> [Coordinate]:
    res = []

    for loc in path:
        res.append(Coordinate(loc.x, loc.y, height))

    return res
