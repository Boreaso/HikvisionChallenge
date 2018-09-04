import time

from simpleai.search import SearchProblem, astar

from model import Coordinate

HORIZONTAL_DIRECTIONS = [(-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0),
                         (-1, 1, 0), (1, 1, 0), (1, -1, 0), (-1, -1, 0)]
VERTICAL_DIRECTIONS = [(0, 0, -1), (0, 0, 1)]


class RoutePlanProblem(SearchProblem):

    def __init__(self, map_range: Coordinate, h_low: int, h_high: int,
                 obstacles: list, fogs=None, three_dim=False):
        """
        初始化地图信息
        :param map_range: 地图 Coordinate对象
        :param h_high: 最大飞行高度
        :param h_low: 最低飞行高度
        :param obstacles: 障碍物 [(x1, y1, x2, y2, z1, z2), ...]
        x1,y1表示障碍物的水平起始坐标， x2, y2表示水平终止坐标（x2=x1+l, y2=y1+w），
        z1,z2分别为垂直旗帜坐标
        :param three_dim: 是否在单位空间搜索路径
        """
        self.map_range = map_range
        self.h_low = h_low
        self.h_high = h_high
        self.obstacles = obstacles
        self.fogs = fogs
        self.end_state = None
        self.three_dim = three_dim
        super().__init__(None)

    def set_config(self, start: Coordinate, end: Coordinate, h_low: int, h_high: int,
                   obstacles=None, map_range: Coordinate = None, three_dim=False):
        """
        设置当前路径的起始点和飞行器所处的高度
        :param start: 路径起点 (start_x, start_y)
        :param end: 路径终点 (end_x, end_y)
        :param h_high: 最大飞行高度
        :param h_low: 最低飞行高度
        :param obstacles: 障碍物（建筑物，无人机）
        :param map_range: 当前地图搜索范围，Coordinate对象
        :param three_dim: 是否在单位空间搜索路径
        """
        self.initial_state = start
        self.end_state = end
        self.h_low = h_low
        self.h_high = h_high
        self.three_dim = three_dim
        if map_range:
            self.map_range = map_range
        if obstacles:
            self.obstacles = obstacles

    def actions(self, state):
        if state != self.end_state:
            actions = []
            if self.three_dim:
                # 三维空间搜索
                if self.h_low <= state.z <= self.h_high:
                    # 可以水平飞行
                    for di in HORIZONTAL_DIRECTIONS:
                        new_state = state + di
                        if new_state.is_valid(self.map_range.x, self.map_range.y, self.map_range.z) and \
                                not new_state.is_overlap(self.obstacles):
                            actions.append(di)
                if state.z <= self.h_low:
                    # 不能小于最低飞行高度，只能往上飞
                    actions.append(VERTICAL_DIRECTIONS[1])
                elif state.z >= self.h_high:
                    # 不能大于最大飞行高度，只能往下飞
                    actions.append(VERTICAL_DIRECTIONS[0])
                elif self.map_range.z > 0:
                    # 垂直方向搜索
                    for di in VERTICAL_DIRECTIONS:
                        new_state = state + di
                        if 0 <= new_state.z <= self.map_range.z:
                            actions.append(di)
            else:
                # 二维空间搜索，不考虑垂直方向
                for di in HORIZONTAL_DIRECTIONS:
                    new_state = state + di
                    if new_state.is_valid(self.map_range.x, self.map_range.y, self.map_range.z) and \
                            not new_state.is_overlap(self.obstacles):
                        actions.append(di)
            return actions
        else:
            return []

    def result(self, state, action):
        return state + action

    def is_goal(self, state):
        return state == self.end_state

    def heuristic(self, state):
        d_x = abs(state.x - self.end_state.x)
        d_y = abs(state.y - self.end_state.y)
        # d_z = abs(state.z - self.end_state.z)
        return d_x + d_y

    def value(self, state):
        pass

    def crossover(self, state1, state2):
        pass

    def mutate(self, state):
        pass

    def generate_random_state(self):
        pass


if __name__ == '__main__':
    search_height = 0
    map_range = Coordinate(99, 99, 0)
    buildings = [(2, 0, 2, 98, 0, 1), (4, 1, 4, 99, 1, 1), (6, 0, 6, 98, 0, 1)]

    start = (1, 0, search_height)
    end = (99, 0, search_height)

    result = None
    count = 1

    problem = RoutePlanProblem(
        map_range=map_range,
        h_low=0,
        h_high=0,
        obstacles=buildings)

    time_start = time.time()

    for _ in range(count):
        problem.set_config(start=Coordinate(*start),
                           end=Coordinate(*end),
                           h_low=0, h_high=1)
        result = astar(problem, graph_search=True)

    time_end = time.time()

    path = [(c.x, c.y, c.z) for (_, c) in result.path()]
    print(result.state)
    print('step: %d' % len(path))
    print('path: %s' % path)
    print('Time: %s s' % ((time_end - time_start) / count))
