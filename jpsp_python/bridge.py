from jpsp_python.jps import Point, Node
from model import Coordinate


def xy_to_point(x, y) -> Point:
    return Point(row=y, col=x)


def point_to_xy(point) -> tuple:
    return point.col, point.row


def buildings_to_obstacle_points(
        buildings: [tuple], height: int) -> [Point]:
    obstacle_points = []

    for building in buildings:
        x1, y1, x2, y2, z1, z2 = building

        if z1 <= height <= z2:
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    point = xy_to_point(x, y)
                    obstacle_points.append(point)

    return obstacle_points


def to_coordinate_path(path: [Point], height) -> [Coordinate]:
    coordinate_path = []
    for point in path:
        x, y = point_to_xy(point)
        coordinate_path.append(Coordinate(x, y, height))
    return coordinate_path


def print_map(grid_nodes: [Node], width, height, start: Point = None, end: Point = None):
    padding = width + 8
    print("\n%s Map %s" % ("#" * padding, "#" * padding))

    # Print x coordinate.
    for i in range(height + 1):
        if i == 0:
            print("   ", end="")
        else:
            print("\033[1;31m%d%s\033[0m" % ((i - 1), " " * (3 - len(str(i)))), end='')
    print()

    for i in range(height):
        print("\033[1;31m%d%s\033[0m" % (i, " " * (3 - len(str(i)))), end='')

        for j in range(width):
            if (start and i == start.row and j == start.col) or \
                    (end and i == end.row and j == end.col):
                print("\033[1;31m%s%s\033[0m" % (int(grid_nodes[j + i * width].is_obstacle), " " * 2), end='')
            else:
                print('%s%s' % (int(grid_nodes[j + i * width].is_obstacle), " " * 2), end='')
        print()

    print("%s Map %s\n" % ("#" * padding, "#" * padding))
