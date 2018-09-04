import heapq
import math


# from model import Coordinate


class BoundedPriorityQueue(object):
    def __init__(self, limit=None, *args):
        self.limit = limit
        self.queue = list()

    def __getitem__(self, val):
        return self.queue[val]

    def __len__(self):
        return len(self.queue)

    def empty(self):
        return len(self.queue) == 0

    def append(self, x):
        heapq.heappush(self.queue, x)
        if self.limit and len(self.queue) > self.limit:
            self.queue.remove(heapq.nlargest(1, self.queue)[0])

    def pop(self):
        return heapq.heappop(self.queue)

    def extend(self, iterable):
        for x in iterable:
            self.append(x)

    def clear(self):
        for x in self:
            self.queue.remove(x)

    def remove(self, x):
        self.queue.remove(x)

    def sorted(self):
        return heapq.nsmallest(len(self.queue), self.queue)


class Point:
    """坐标运算类"""

    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.row == other.row and self.col == other.col

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        return self.__class__(self.row, self.col)

    def __add__(self, other):
        if isinstance(other, self.__class__):
            row = self.row + other.row
            col = self.col + other.col
        elif isinstance(other, tuple) and len(other) == 3:
            row = self.row + other[0]
            col = self.col + other[1]
        else:
            row = col = -1
        return self.__class__(row, col)

    def __sub__(self, other):
        if isinstance(other, self.__class__):
            row = self.row - other.row
            col = self.col - other.col
        elif isinstance(other, tuple) and len(other) == 3:
            row = self.row - other[0]
            col = self.col - other[1]
        else:
            row = col = -1
        return self.__class__(row, col)

    def __hash__(self):
        return hash('%d%d' % (self.row, self.col))

    def __str__(self):
        return "(%d, %d)" % (self.row, self.col)

    @staticmethod
    def diff(a, b):
        return max(abs(b.row - a.row), abs(b.col - a.col))


class Direction:
    NORTH = 0
    NORTH_EAST = 1
    EAST = 2
    SOUTH_EAST = 3
    SOUTH = 4
    SOUTH_WEST = 5
    WEST = 6
    NORTH_WEST = 7

    @staticmethod
    def all_directions():
        return [i for i in range(8)]

    @staticmethod
    def is_cardinal(dir: int):
        if dir == Direction.NORTH or \
                dir == Direction.EAST or \
                dir == Direction.SOUTH or \
                dir == Direction.WEST:
            return True
        return False

    @staticmethod
    def is_diagonal(dir: int):
        if dir == Direction.NORTH_EAST or \
                dir == Direction.NORTH_WEST or \
                dir == Direction.SOUTH_EAST or \
                dir == Direction.SOUTH_WEST:
            return True
        return False

    @staticmethod
    def dir_to_string(dir):
        if dir == Direction.NORTH:
            return "NORTH"
        elif dir == Direction.NORTH_EAST:
            return "NORTH_WEST"
        elif dir == Direction.EAST:
            return "EAST"
        elif dir == Direction.SOUTH_EAST:
            return "SOUTH_EAST"
        elif dir == Direction.SOUTH:
            return "SOUTH"
        elif dir == Direction.SOUTH_WEST:
            return "SOUTH_WEST"
        elif dir == Direction.WEST:
            return "WEST"
        elif dir == Direction.NORTH_WEST:
            return "NORTH_WEST"
        else:
            return "NONE"


class Node:
    """运算节点类"""

    def __init__(self, pos=None):
        self.pos: Point = pos
        self.is_obstacle: bool = False
        self.jp_distances: list = [0] * 8
        self.is_jump_point: bool = False
        # 如果当前节点是一个PrimaryPoint, 那么jump_point_direction指的是当前
        # PrimaryPoint可以由哪个方向到达，如jump_point_direction[East]指的是
        # 当前节点是否可以从右边的路径达到
        self.jump_point_direction = [False] * 8

    def is_jump_point_from(self, dir: int):
        return self.is_jump_point and self.jump_point_direction[dir]


class ListStatus:
    ON_NONE = 0
    ON_OPEN = 1
    ON_CLOSED = 2


class PathFindingNode:
    """路径搜索时节点"""

    def __init__(self, pos=None):
        self.parent: PathFindingNode = None
        self.pos: Point = pos
        self.given_cost: int = 0
        self.final_cost: int = 0
        self.direction_from_parent: int = -1
        self.list_status: ListStatus = ListStatus.ON_NONE

    def __lt__(self, other):
        """构建最小优先权队列使用"""
        return self.final_cost < other.final_cost

    def __le__(self, other):
        """构建最小优先权队列使用"""
        return self.final_cost <= other.final_cost

    def reset(self):
        self.parent = None
        self.given_cost = 0
        self.final_cost = 0
        self.list_status = ListStatus.ON_NONE


class PathFindStatus:
    SEARCHING = 0
    FOUND = 1
    NOT_FOUND = 2


class PathFindReturn:
    """路径搜索结果"""

    def __init__(self):
        self.current: PathFindingNode = None
        self.status: PathFindStatus = PathFindStatus.SEARCHING
        self.path: [Point] = []


class JPS:
    """Jump Point Search算法封装"""

    VALID_DIRECTION_LOOK_UP_TABLE = \
        {
            Direction.SOUTH: [Direction.WEST, Direction.SOUTH_WEST, Direction.SOUTH, Direction.SOUTH_EAST,
                              Direction.EAST],
            Direction.SOUTH_EAST: [Direction.SOUTH, Direction.SOUTH_EAST, Direction.EAST],
            Direction.EAST: [Direction.SOUTH, Direction.SOUTH_EAST, Direction.EAST, Direction.NORTH_EAST,
                             Direction.NORTH],
            Direction.NORTH_EAST: [Direction.EAST, Direction.NORTH_EAST, Direction.NORTH],
            Direction.NORTH: [Direction.EAST, Direction.NORTH_EAST, Direction.NORTH, Direction.NORTH_WEST,
                              Direction.WEST],
            Direction.NORTH_WEST: [Direction.NORTH, Direction.NORTH_WEST, Direction.WEST],
            Direction.WEST: [Direction.NORTH, Direction.NORTH_WEST, Direction.WEST, Direction.SOUTH_WEST,
                             Direction.SOUTH],
            Direction.SOUTH_WEST: [Direction.WEST, Direction.SOUTH_WEST, Direction.SOUTH],
        }

    SQRT_2 = math.sqrt(2)
    SQRT_2_MINUS_1 = math.sqrt(2) - 1

    def __init__(self, width, height, obstacles: [Point]):
        self.grid_nodes = [
            Node(Point(i // width, i % width)) for i in range(width * height)]
        self.path_finding_nodes = [
            PathFindingNode(Point(i // width, i % width)) for i in range(width * height)]
        self.row_size: int = width
        self.max_rows: int = height

        # 初始化障碍物
        for point in obstacles:
            if self._is_in_bounds_rc(point.row, point.col):
                index = point.col + point.row * self.row_size
                self.grid_nodes[index].is_obstacle = True

    def _get_north_east_index(self, row, col):
        if col + 1 >= self.row_size or row - 1 < 0:
            return -1
        return (col + 1) + (row - 1) * self.row_size

    def _get_south_east_index(self, row, col):
        if col + 1 >= self.row_size or row + 1 >= self.max_rows:
            return -1
        return (col + 1) + (row + 1) * self.row_size

    def _get_south_west_index(self, row, col):
        if col - 1 < 0 or row + 1 >= self.max_rows:
            return -1
        return (col - 1) + (row + 1) * self.row_size

    def _get_north_west_index(self, row, col):
        if col - 1 < 0 or row - 1 < 0:
            return -1
        return (col - 1) + (row - 1) * self.row_size

    def _get_north_index(self, row, col):
        if row - 1 < 0:
            return -1
        return col + (row - 1) * self.row_size

    def _get_east_index(self, row, col):
        if col + 1 >= self.row_size:
            return -1
        return (col + 1) + row * self.row_size

    def _get_south_index(self, row, col):
        if row + 1 >= self.max_rows:
            return -1
        return col + (row + 1) * self.row_size

    def _get_west_index(self, row, col):
        if col - 1 < 0:
            return -1
        return (col - 1) + row * self.row_size

    def _row_col_to_index(self, row, col):
        return col + row * self.row_size

    def _point_to_index(self, pos: Point):
        return self._row_col_to_index(pos.row, pos.col)

    def _is_in_bounds_rc(self, row, col):
        return 0 <= row < self.max_rows and \
               0 <= col < self.row_size

    def _is_in_bounds(self, index):
        if index < 0 or index >= len(self.grid_nodes):
            return False
        row = index // self.row_size
        col = index % self.row_size
        return self._is_in_bounds_rc(row, col)

    def _is_obstacle_or_wall_rc(self, row, col):
        return self._is_in_bounds_rc(row, col) and \
               self.grid_nodes[self._row_col_to_index(row, col)].is_obstacle

    def _is_obstacle_or_wall(self, index):
        if index < 0:
            return True
        row = index // self.row_size
        col = index % self.row_size
        return self._is_obstacle_or_wall_rc(row, col)

    def _is_empty_rc(self, row, col):
        return not self._is_obstacle_or_wall_rc(row, col)

    def _is_empty(self, index: int):
        if index < 0:
            return False
        row = index // self.row_size
        col = index % self.row_size
        return self._is_empty_rc(row, col)

    def _get_index_of_node_toward_direction(self, index, direction: int):
        """ 计算指定方向的index， -1表示越界。"""

        row = index // self.row_size
        col = index % self.row_size
        change_row, change_col = 0, 0

        # 计算行方向
        if direction == Direction.NORTH or \
                direction == Direction.NORTH_WEST or \
                direction == Direction.NORTH_EAST:
            change_row = -1
        elif direction == Direction.SOUTH or \
                direction == Direction.SOUTH_WEST or \
                direction == Direction.SOUTH_EAST:
            change_row = 1

        # 计算列方向
        if direction == Direction.EAST or \
                direction == Direction.NORTH_EAST or \
                direction == Direction.SOUTH_EAST:
            change_col = 1
        elif direction == Direction.WEST or \
                direction == Direction.NORTH_WEST or \
                direction == Direction.SOUTH_WEST:
            change_col = -1

        # 新的行列
        new_row = row + change_row
        new_col = col + change_col

        # 边界检查
        if self._is_in_bounds_rc(row, col):
            return new_col + new_row * self.row_size

        return -1

    def _get_node(self, row, col):
        if self._is_in_bounds_rc(row, col):
            index = self._row_col_to_index(row, col)
            return self.grid_nodes[index]
        else:
            return Node

    def build_primary_points(self):
        """计算JPS算法的PrimaryPoints。"""

        # 遍历每个障碍物
        for i, current_node in enumerate(self.grid_nodes):
            row = i // self.row_size
            col = i % self.row_size

            if current_node.is_obstacle:
                # NORTH
                north_index = self._get_north_index(row, col)
                if north_index != -1:
                    node = self.grid_nodes[north_index]
                    if not node.is_obstacle:
                        toward_south_east = self._get_index_of_node_toward_direction(north_index, Direction.SOUTH_EAST)
                        toward_south_west = self._get_index_of_node_toward_direction(north_index, Direction.SOUTH_WEST)
                        toward_east = self._get_index_of_node_toward_direction(north_index, Direction.EAST)
                        toward_west = self._get_index_of_node_toward_direction(north_index, Direction.WEST)
                        if self._is_empty(toward_west) and self._is_empty(toward_south_east):
                            node.is_jump_point = True
                            node.jump_point_direction[Direction.WEST] = True
                        if self._is_empty(toward_east) and self._is_empty(toward_south_west):
                            node.is_jump_point = True
                            node.jump_point_direction[Direction.EAST] = True
                        if self._is_empty(toward_south_west) and self._is_empty(toward_south_east):
                            node.is_jump_point = True

                # EAST
                east_index = self._get_east_index(row, col)
                if east_index != -1:
                    node = self.grid_nodes[east_index]
                    if not node.is_obstacle:
                        toward_north_west = self._get_index_of_node_toward_direction(east_index, Direction.NORTH_WEST)
                        toward_south_west = self._get_index_of_node_toward_direction(east_index, Direction.SOUTH_WEST)
                        toward_north = self._get_index_of_node_toward_direction(east_index, Direction.NORTH)
                        toward_south = self._get_index_of_node_toward_direction(east_index, Direction.SOUTH)
                        if self._is_empty(toward_north_west) and self._is_empty(toward_south):
                            node.is_jump_point = True
                            node.jump_point_direction[Direction.SOUTH] = True
                        if self._is_empty(toward_south_west) and self._is_empty(toward_north):
                            node.is_jump_point = True
                            node.jump_point_direction[Direction.NORTH] = True
                        if self._is_empty(toward_north_west) and self._is_empty(toward_south_west):
                            node.is_jump_point = True

                # SOUTH
                south_index = self._get_south_index(row, col)
                if south_index != -1:
                    node = self.grid_nodes[south_index]
                    if not node.is_obstacle:
                        toward_north_west = self._get_index_of_node_toward_direction(south_index, Direction.NORTH_WEST)
                        toward_north_east = self._get_index_of_node_toward_direction(south_index, Direction.NORTH_EAST)
                        toward_west = self._get_index_of_node_toward_direction(south_index, Direction.WEST)
                        toward_east = self._get_index_of_node_toward_direction(south_index, Direction.EAST)
                        if self._is_empty(toward_north_west) and self._is_empty(toward_east):
                            node.is_jump_point = True
                            node.jump_point_direction[Direction.EAST] = True
                        if self._is_empty(toward_north_east) and self._is_empty(toward_west):
                            node.is_jump_point = True
                            node.jump_point_direction[Direction.WEST] = True
                        if self._is_empty(toward_north_west) and self._is_empty(toward_north_east):
                            node.is_jump_point = True

                # WEST
                west_index = self._get_west_index(row, col)
                if west_index != -1:
                    node = self.grid_nodes[west_index]
                    if not node.is_obstacle:
                        toward_south_east = self._get_index_of_node_toward_direction(west_index, Direction.SOUTH_EAST)
                        toward_north_east = self._get_index_of_node_toward_direction(west_index, Direction.NORTH_EAST)
                        toward_north = self._get_index_of_node_toward_direction(west_index, Direction.NORTH)
                        toward_south = self._get_index_of_node_toward_direction(west_index, Direction.SOUTH)
                        if self._is_empty(toward_south_east) and self._is_empty(toward_north):
                            node.is_jump_point = True
                            node.jump_point_direction[Direction.NORTH] = True
                        if self._is_empty(toward_north_east) and self._is_empty(toward_south):
                            node.is_jump_point = True
                            node.jump_point_direction[Direction.SOUTH] = True
                        if self._is_empty(toward_north_east) and self._is_empty(toward_south_east):
                            node.is_jump_point = True

    def build_strait_jump_points(self):
        # 遍历每一行，计算 left 和 right 方向的Jump Distance
        for row in range(self.max_rows):
            # 从 left 到 right
            jump_distance_so_far = -1
            jump_point_seen = False
            # 计算往 WEST 方向移动的 Jump Distance
            for col in range(self.row_size):
                node = self._get_node(row, col)
                if node.is_obstacle:
                    jump_distance_so_far = -1
                    jump_point_seen = False
                    node.jp_distances[Direction.WEST] = 0
                    continue
                # 距离进行累加
                jump_distance_so_far += 1
                if jump_point_seen:
                    # 左边有JumpPoint，那么当前节点的左边方向的距离值为到JumpPoint的距离
                    node.jp_distances[Direction.WEST] = jump_distance_so_far
                else:
                    # 没有JumpPoint，那么赋予距离障碍物的距离，负数表示
                    node.jp_distances[Direction.WEST] = -jump_distance_so_far
                if node.is_jump_point_from(Direction.EAST):
                    # 当前节点是新的JumpPoint
                    jump_distance_so_far = 0
                    jump_point_seen = True

            # 从 right 到 left
            jump_distance_so_far = -1
            jump_point_seen = False
            # 计算往 EAST 方向移动的 Jump Distance
            for col in reversed(range(self.row_size)):
                node = self._get_node(row, col)
                if node.is_obstacle:
                    jump_distance_so_far = -1
                    jump_point_seen = False
                    node.jp_distances[Direction.EAST] = 0
                    continue
                # 距离进行累加
                jump_distance_so_far += 1
                if jump_point_seen:
                    # 左边有JumpPoint，那么当前节点的左边方向的距离值为到JumpPoint的距离
                    node.jp_distances[Direction.EAST] = jump_distance_so_far
                else:
                    # 没有JumpPoint，那么赋予距离障碍物的距离，负数表示
                    node.jp_distances[Direction.EAST] = -jump_distance_so_far
                if node.is_jump_point_from(Direction.WEST):
                    # 当前节点是新的JumpPoint
                    jump_distance_so_far = 0
                    jump_point_seen = True

        # 遍历每一列，计算 up 和 down 方向的Jump Distance
        for col in range(self.row_size):
            # 从 up 到 down 方向
            jump_distance_so_far = -1
            jump_point_seen = False
            # 计算往 NORTH 方向移动的 Jump Distance
            for row in range(self.max_rows):
                node = self._get_node(row, col)
                if node.is_obstacle:
                    jump_distance_so_far = -1
                    jump_point_seen = False
                    node.jp_distances[Direction.NORTH] = 0
                    continue
                # 距离进行累加
                jump_distance_so_far += 1
                if jump_point_seen:
                    # up方向有JumpPoint，那么当前节点的左边方向的距离值为到JumpPoint的距离
                    node.jp_distances[Direction.NORTH] = jump_distance_so_far
                else:
                    # 没有JumpPoint，那么赋予距离障碍物的距离，负数表示
                    node.jp_distances[Direction.NORTH] = -jump_distance_so_far
                if node.is_jump_point_from(Direction.SOUTH):
                    # 当前节点是新的JumpPoint
                    jump_distance_so_far = 0
                    jump_point_seen = True

            # 从 down 到 up
            jump_distance_so_far = -1
            jump_point_seen = False
            # 计算往 SOUTH 方向移动的 Jump Distance
            for row in reversed(range(self.max_rows)):
                node = self._get_node(row, col)
                if node.is_obstacle:
                    jump_distance_so_far = -1
                    jump_point_seen = False
                    node.jp_distances[Direction.SOUTH] = 0
                    continue
                # 距离进行累加
                jump_distance_so_far += 1
                if jump_point_seen:
                    # 左边有JumpPoint，那么当前节点的左边方向的距离值为到JumpPoint的距离
                    node.jp_distances[Direction.SOUTH] = jump_distance_so_far
                else:
                    # 没有JumpPoint，那么赋予距离障碍物的距离，负数表示
                    node.jp_distances[Direction.SOUTH] = -jump_distance_so_far
                if node.is_jump_point_from(Direction.NORTH):
                    # 当前节点是新的JumpPoint
                    jump_distance_so_far = 0
                    jump_point_seen = True

    def build_diagonal_jump_points(self):
        """计算斜角方向的 Jump Distance."""

        # 计算 UpLeft 和 UpRight 方向的斜角距离
        for row in range(self.max_rows):
            # 遍历列
            for col in range(self.row_size):
                # 如果是障碍，略过
                if self._is_obstacle_or_wall_rc(row, col):
                    continue
                node = self._get_node(row, col)

                # NORTH_WEST Distances，允许障碍物的拐角斜走
                if row == 0 or col == 0 or \
                        self._is_obstacle_or_wall_rc(row - 1, col - 1):
                    # NORTH_WEST不可走
                    node.jp_distances[Direction.NORTH_WEST] = 0
                elif self._get_node(row - 1, col - 1).jp_distances[Direction.NORTH] > 0 or \
                        self._get_node(row - 1, col - 1).jp_distances[Direction.WEST] > 0 or \
                        self._get_node(row - 1, col - 1).is_jump_point:
                    # 可以连接到正方向行走的节点
                    node.jp_distances[Direction.NORTH_WEST] = 1
                else:
                    # 斜角方向距离递增
                    jp_distance = self._get_node(row - 1, col - 1).jp_distances[Direction.NORTH_WEST]
                    if jp_distance > 0:
                        node.jp_distances[Direction.NORTH_WEST] = jp_distance + 1
                    else:
                        node.jp_distances[Direction.NORTH_WEST] = jp_distance - 1

                # NORTH_EAST Distances，允许障碍物的拐角斜走
                if row == 0 or col == self.row_size - 1 or \
                        self._is_obstacle_or_wall_rc(row - 1, col + 1):
                    # NORTH_EAST不可走
                    node.jp_distances[Direction.NORTH_EAST] = 0
                elif self._get_node(row - 1, col + 1).jp_distances[Direction.NORTH] > 0 or \
                        self._get_node(row - 1, col + 1).jp_distances[Direction.EAST] > 0 or \
                        self._get_node(row - 1, col + 1).is_jump_point:
                    # 可以连接到正方向行走的节点
                    node.jp_distances[Direction.NORTH_EAST] = 1
                else:
                    # 斜角方向距离递增
                    jp_distance = self._get_node(row - 1, col + 1).jp_distances[Direction.NORTH_EAST]
                    if jp_distance > 0:
                        node.jp_distances[Direction.NORTH_EAST] = jp_distance + 1
                    else:
                        node.jp_distances[Direction.NORTH_EAST] = jp_distance - 1

        # 计算 DownLeft 和 DownRight 方向的斜角距离
        for row in reversed(range(self.max_rows)):
            # 遍历列
            for col in range(self.row_size):
                # 如果是障碍，略过
                if self._is_obstacle_or_wall_rc(row, col):
                    continue
                node = self._get_node(row, col)

                # SOUTH_WEST Distances，允许障碍物的拐角斜走
                if row == self.max_rows - 1 or col == 0 or \
                        self._is_obstacle_or_wall_rc(row + 1, col - 1):
                    # SOUTH_WEST不可走
                    node.jp_distances[Direction.SOUTH_WEST] = 0
                elif self._get_node(row + 1, col - 1).jp_distances[Direction.SOUTH] > 0 or \
                        self._get_node(row + 1, col - 1).jp_distances[Direction.WEST] > 0 or \
                        self._get_node(row + 1, col - 1).is_jump_point:
                    # 可以连接到正方向行走的节点
                    node.jp_distances[Direction.SOUTH_WEST] = 1
                else:
                    # 斜角方向距离递增
                    jp_distance = self._get_node(row + 1, col - 1).jp_distances[Direction.SOUTH_WEST]
                    if jp_distance > 0:
                        node.jp_distances[Direction.SOUTH_WEST] = jp_distance + 1
                    else:
                        node.jp_distances[Direction.SOUTH_WEST] = jp_distance - 1

                # SOUTH_EAST Distances，允许障碍物的拐角斜走
                if row == self.max_rows - 1 or col == self.row_size - 1 or \
                        self._is_obstacle_or_wall_rc(row + 1, col + 1):
                    # SOUTH_EAST不可走
                    node.jp_distances[Direction.SOUTH_EAST] = 0
                elif self._get_node(row + 1, col + 1).jp_distances[Direction.SOUTH] > 0 or \
                        self._get_node(row + 1, col + 1).jp_distances[Direction.EAST] > 0 or \
                        self._get_node(row + 1, col + 1).is_jump_point:
                    # 可以连接到正方向行走的节点
                    node.jp_distances[Direction.SOUTH_EAST] = 1
                else:
                    # 斜角方向距离递增
                    jp_distance = self._get_node(row + 1, col + 1).jp_distances[Direction.SOUTH_EAST]
                    if jp_distance > 0:
                        node.jp_distances[Direction.SOUTH_EAST] = jp_distance + 1
                    else:
                        node.jp_distances[Direction.SOUTH_EAST] = jp_distance - 1

    @staticmethod
    def octile_heuristic(cur_row, cur_col, goal_row, goal_col):
        # 斜角距离启发函数
        return max(abs(cur_row - goal_row), abs(cur_col - goal_col))

    def _get_all_valid_directions(self, pf_node: PathFindingNode):
        # 获得合法的方向
        return self.VALID_DIRECTION_LOOK_UP_TABLE[pf_node.direction_from_parent] \
            if pf_node.parent else Direction.all_directions()

    @staticmethod
    def goal_is_in_exact_direction(cur: Point, dir: int, goal: Point):
        diff_row = goal.row - cur.row
        diff_col = goal.col - cur.col
        if dir == Direction.NORTH:
            return diff_row < 0 and diff_col == 0
        elif dir == Direction.NORTH_EAST:
            return diff_row < 0 and diff_col > 0 and abs(diff_row) == abs(diff_col)
        elif dir == Direction.EAST:
            return diff_row == 0 and diff_col > 0
        elif dir == Direction.SOUTH_EAST:
            return diff_row > 0 and diff_col > 0 and abs(diff_row) == abs(diff_col)
        elif dir == Direction.SOUTH:
            return diff_row > 0 and diff_col == 0
        elif dir == Direction.SOUTH_WEST:
            return diff_row > 0 and diff_col < 0 and abs(diff_row) == abs(diff_col)
        elif dir == Direction.WEST:
            return diff_row == 0 and diff_col < 0
        elif dir == Direction.NORTH_WEST:
            return diff_row < 0 and diff_col < 0 and abs(diff_row) == abs(diff_col)
        return False

    @staticmethod
    def goal_is_in_general_direction(cur: Point, dir: int, goal: Point):
        diff_row = goal.row - cur.row
        diff_col = goal.col - cur.col
        if dir == Direction.NORTH:
            return diff_row < 0 and diff_col == 0
        elif dir == Direction.NORTH_EAST:
            return diff_row < 0 and diff_col > 0
        elif dir == Direction.EAST:
            return diff_row == 0 and diff_col > 0
        elif dir == Direction.SOUTH_EAST:
            return diff_row > 0 and diff_col > 0
        elif dir == Direction.SOUTH:
            return diff_row > 0 and diff_col == 0
        elif dir == Direction.SOUTH_WEST:
            return diff_row > 0 and diff_col < 0
        elif dir == Direction.WEST:
            return diff_row == 0 and diff_col < 0
        elif dir == Direction.NORTH_WEST:
            return diff_row < 0 and diff_col < 0
        return False

    def _get_node_dist(self, row, col, dir, dist):
        """获得指定方向的PathFindingNode节点
        :rtype PathFindingNode
        """
        new_node = None
        new_row, new_col = row, col

        if dir == Direction.NORTH:
            new_row -= dist
        elif dir == Direction.NORTH_EAST:
            new_row -= dist
            new_col += dist
        elif dir == Direction.EAST:
            new_col += dist
        elif dir == Direction.SOUTH_EAST:
            new_row += dist
            new_col += dist
        elif dir == Direction.SOUTH:
            new_row += dist
        elif dir == Direction.SOUTH_WEST:
            new_row += dist
            new_col -= dist
        elif dir == Direction.WEST:
            new_col -= dist
        elif dir == Direction.NORTH_WEST:
            new_row -= dist
            new_col -= dist

        if self._is_in_bounds_rc(new_row, new_col):
            index = self._row_col_to_index(new_row, new_col)
            new_node = self.path_finding_nodes[index]

        return new_node

    @staticmethod
    def reconstruct_path(goal: Node, start: Point) -> [Point]:
        """逆序构建路径列表"""
        path = []
        cur_node = goal
        while cur_node.parent:
            path.append(cur_node.pos)
            cur_node = cur_node.parent
        # 把开始节点一并加入
        path.append(start)
        return path[::-1]

    @staticmethod
    def reconstruct_full_path(goal: Node, start: Point) -> [Point]:
        final_path = []
        cur_node = goal
        while cur_node:
            final_path.append(cur_node.pos)
            parent = cur_node.parent
            if parent:
                x_diff = parent.pos.col - cur_node.pos.col
                y_diff = parent.pos.row - cur_node.pos.row
                x_inc, y_inc = 0, 0

                if x_diff > 0:
                    x_inc = 1
                elif x_diff < 0:
                    x_inc = -1
                    x_diff = -x_diff

                if y_diff > 0:
                    y_inc = 1
                elif y_diff < 0:
                    y_inc = -1
                    y_diff = -y_diff

                x, y = cur_node.pos.col, cur_node.pos.row
                steps = x_diff - 1
                if y_diff > x_diff:
                    steps = y_diff - 1

                for _ in range(steps):
                    x += x_inc
                    y += y_inc
                    final_path.append(Point(y, x))

            cur_node = cur_node.parent

        assert final_path[-1] == start

        for i in range(len(final_path) - 1):
            if abs(final_path[i + 1].row - final_path[i].row) > 1 or \
                    abs(final_path[i + 1].col - final_path[i].col) > 1:
                break

        return final_path[::-1]

    def _reset_path_finding_node_data(self):
        for node in self.path_finding_nodes:
            node.reset()

    def get_path(self, start: Point, goal: Point, full_path=True) -> [Point]:
        """根据预处理数据获得start->goal路径。"""
        path = []
        open_set = BoundedPriorityQueue()

        # 重置历史数据
        self._reset_path_finding_node_data()
        starting_node = self.path_finding_nodes[self._point_to_index(start)]
        starting_node.pos = start
        starting_node.parent = None
        starting_node.given_cost = 0
        starting_node.final_cost = 0
        starting_node.list_status = ListStatus.ON_OPEN

        # 添加初始节点
        open_set.append(starting_node)

        while not open_set.empty():
            cur_node = open_set.pop()
            jp_node = self._get_node(cur_node.pos.row, cur_node.pos.col)

            # 检查是否到达终点
            if cur_node.pos == goal:
                if full_path:
                    path = self.reconstruct_full_path(cur_node, start)
                else:
                    path = self.reconstruct_path(cur_node, start)
                break

            # 遍历所有方向
            for dir in Direction.all_directions():
                new_successor = None
                given_cost = 0

                # 目标比障碍物距离更接近，或者小于等于跳点距离
                if Direction.is_cardinal(dir) and \
                        self.goal_is_in_exact_direction(cur_node.pos, dir, goal) and \
                        Point.diff(cur_node.pos, goal) <= abs(jp_node.jp_distances[dir]):
                    new_successor = self.path_finding_nodes[self._point_to_index(goal)]
                    given_cost = cur_node.given_cost + Point.diff(cur_node.pos, goal)
                elif Direction.is_diagonal(dir) and \
                        self.goal_is_in_general_direction(cur_node.pos, dir, goal) and \
                        (abs(goal.row - cur_node.pos.row) <= abs(jp_node.jp_distances[dir]) or
                         abs(goal.col - cur_node.pos.col) <= abs(jp_node.jp_distances[dir])):
                    min_diff = min(abs(goal.row - cur_node.pos.row),
                                   abs(goal.col - cur_node.pos.col))
                    new_successor = self._get_node_dist(
                        cur_node.pos.row, cur_node.pos.col, dir, min_diff)
                    given_cost = cur_node.given_cost + Point.diff(cur_node.pos, new_successor.pos)
                elif jp_node.jp_distances[dir] > 0:
                    new_successor = self._get_node_dist(
                        cur_node.pos.row, cur_node.pos.col, dir, jp_node.jp_distances[dir])
                    given_cost = Point.diff(cur_node.pos, new_successor.pos)

                    # if Direction.is_diagonal(dir):
                    #     given_cost *= self.SQRT_2

                    given_cost += cur_node.given_cost

                if new_successor and \
                        (new_successor.list_status != ListStatus.ON_OPEN or
                         given_cost < new_successor.given_cost):
                    new_successor.parent = cur_node
                    new_successor.given_cost = given_cost
                    new_successor.direction_from_parent = dir
                    new_successor.final_cost = given_cost + self.octile_heuristic(
                        new_successor.pos.row, new_successor.pos.col, goal.row, goal.col)
                    new_successor.list_status = ListStatus.ON_OPEN
                    open_set.append(new_successor)

        return path
