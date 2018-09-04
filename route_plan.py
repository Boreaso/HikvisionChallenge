import sys
import time

import numpy as np
from simpleai.search import astar

from env import env
from jpsp_c_api import jpsp_bridge as bridge
# from jpsp_boost.jpsp_bridge import loc_path_to_coordinate_path, xy_to_loc
from model import Coordinate, Goods, MapInfo, StepInfo, UAV
from search import HORIZONTAL_DIRECTIONS, RoutePlanProblem, VERTICAL_DIRECTIONS


# Agent status状态码
class TaskType:
    NO_TASK = 0  # 无任务
    TO_GOODS_START = 1  # 前往货物出现点
    TO_GOODS_END = 2  # 前往货物目标点
    TO_CHARGE = 3  # 前往停机坪充电
    TO_RANDOM_POINT = 4  # 前往随机分配的地点
    ATTACK_ENEMY = 5  # 正在执行攻击任务


# 任务优先级，值越大越应该优先执行
PRIORITY_TABLE = {
    TaskType.NO_TASK: 0,
    TaskType.TO_RANDOM_POINT: 1,
    TaskType.TO_CHARGE: 2,
    TaskType.ATTACK_ENEMY: 3,
    TaskType.TO_GOODS_END: 4,
    TaskType.TO_GOODS_START: 5,
}


class TaskPriority:

    @staticmethod
    def look_up(task_type: int):
        return PRIORITY_TABLE[task_type]


class Usage:
    NORMAL = 0  # 可用于运货或者攻击
    ATTACK = 1  # 专门用于攻击，不考虑充电


class DetourMode:
    # Agent take_detour规避模式
    VERTICAL = 3
    HORIZONTAL = 4
    AUTO = 5


DIST_ESTIMATE_RATE = 1.1


def diagonal_distance(start: Coordinate, end: Coordinate):
    return max(abs(start.x - end.x), abs(start.y - end.y))


def diagonal_dis_3d(start: Coordinate, end: Coordinate, h_low: int):
    return max(abs(start.x - end.x), abs(start.y - end.y)) + \
           abs(start.z - h_low) + abs(end.z - h_low)


def manhattan_distance(start: Coordinate, end: Coordinate):
    return abs(start.x - end.x) + abs(start.y - end.y)


def manhattan_dis_3d(start: Coordinate, end: Coordinate, h_low: int):
    return abs(start.x - end.x) + abs(start.y - end.y) + \
           abs(start.z - h_low) + abs(end.z - h_low)


def is_encounter(cur_a: Coordinate, next_a: Coordinate,
                 cur_b: Coordinate, next_b: Coordinate):
    """
    判断两个无人机A，B是否会相遇(包括碰撞)
    :param cur_a: 无人机A当前坐标
    :param next_a: 无人机A下一步坐标
    :param cur_b: 无人机B当前坐标
    :param next_b: 无人机B下一步坐标
    :return: True or False
    """
    if not cur_a or not next_a or not cur_b or not next_b:
        return False
    if next_a == next_b:
        # 碰撞的情况
        return True
    if cur_a == next_b and cur_b == next_a:
        # 交换位置的情况，相遇
        return True
    if cur_a.z == cur_b.z == next_a.z == next_b.z and \
            (abs(cur_a.x - cur_b.x) + abs(cur_a.y - cur_b.y)) == 1:
        # 同一平面内相邻的两个无人机，在一个田字格内同时交叉飞行的情况
        if cur_a.x == cur_b.x and next_a.x == next_b.x and cur_a.x != next_a.x and \
                next_a.y == cur_b.y and next_b.y == cur_a.y:
            return True
        if cur_a.y == cur_b.y and next_a.y == next_b.y and cur_a.y != next_a.y and \
                next_a.x == cur_b.x and next_b.x == cur_a.x:
            return True
    return False


class Agent:
    """路径规划类，每个UAV对应一个Agent，保存实时路径规划信息。"""

    def __init__(self, uav: UAV, map_info: MapInfo):
        """
        :param uav: 对应无人机类对象
        :param map_info: 地图信息
        :param jps_finders: JPS对象字典
        """
        self.uav = uav
        self.map_info = map_info
        self.problem = RoutePlanProblem(
            map_range=self.map_info.map_range,
            h_low=self.map_info.h_low,
            h_high=self.map_info.h_high,
            obstacles=self.map_info.buildings)
        self.path = None  # a list of points(Coordinate obj)
        self.index = 1  # 当前路径节点的索引，第0个为起始点，不用包含在返回路径中
        self.task_type = TaskType.NO_TASK  # Agent任务类型: 见TaskType
        self.task_priority = TaskPriority.look_up(TaskType.NO_TASK)

        # 记录攻击目标
        self.attack_target = None

        self.goods = None  # 已经分配的货物
        self.next_step = None  # 缓存下一步的坐标
        self.usage = Usage.NORMAL

        # 其他参数
        self.approaching_threshold = self.map_info.map_range.x // 30
        if self.approaching_threshold < 1:
            self.approaching_threshold = 1

    def __gt__(self, other):
        """加入优先权队列使用，大价值的无人机优先充电"""
        return self.uav.price > other.uav.price

    def update_uav_info(self, uav: UAV):
        # 根据服务器返回的StepInfo更新无人机信息
        self.uav.assign(uav)

    def update_electricity(self, goods: dict):
        # 更新电量信息
        if self.next_step == self.map_info.parking:
            # or self.status == 3:
            # 充电状态，临界值为下一步要进入停机坪，规则是要充一次电
            price_obj = self.map_info.uav_price[self.uav.uav_type]
            if self.uav.remain_electricity + price_obj.charge >= price_obj.capacity:
                self.uav.remain_electricity = price_obj.capacity
            else:
                self.uav.remain_electricity += price_obj.charge
        elif self.uav.goods_no != -1 or (self.goods and self.next_step == self.goods.end):
            # 载货状态.临界值：取货进入的一步需要扣一次电
            if self.uav.remain_electricity - self.goods.weight <= 0:
                self.uav.remain_electricity = 0
            else:
                self.uav.remain_electricity -= self.goods.weight

    @property
    def price_level(self):
        """当前无人机的价值等级"""
        return self.map_info.price_order.index(self.uav.uav_type)

    @property
    def full_charged(self):
        """电量是否已充满"""
        price_obj = self.map_info.uav_price[self.uav.uav_type]
        return self.uav.remain_electricity == price_obj.capacity

    @property
    def num_remain_steps(self):
        """当前路径剩余步数"""
        if not self.path:
            return 0
        return len(self.path) - self.index

    @property
    def leaving_parking(self):
        """判断当前无人机是否处于离开基地执行任务的状态"""
        if self.task_type != TaskType.NO_TASK and \
                self.task_type != TaskType.TO_CHARGE and \
                self.uav.loc.xy_equal(self.map_info.parking) and \
                0 < self.uav.loc.z <= self.map_info.h_low:
            return True
        return False

    def battery_life(self, weight):
        """获得当前电量续航时间"""
        if not weight:
            # 空载状态，耗电忽略不计
            return sys.maxsize
        else:
            return self.uav.remain_electricity // weight

    def battery_enough(self, weight: int, start: Coordinate, end: Coordinate):
        """根据曼哈顿距离估计电量是否充足"""
        dist = manhattan_dis_3d(start, end, self.map_info.h_low)
        dist = int(dist * DIST_ESTIMATE_RATE)
        return True if self.battery_life(weight) >= dist else False

    def estimate_earnings(self, goods_obj: Goods):
        if goods_obj:
            dist_1 = manhattan_dis_3d(self.uav.loc, goods_obj.start, self.map_info.h_low)
            dist_2 = manhattan_dis_3d(goods_obj.start, goods_obj.end, self.map_info.h_low)
            dist = dist_1 + dist_2
            return goods_obj.value / dist  # 每一步的收益
        return 0

    # def need_to_charge(self, goods_objs: list):
    #     """判断当前无人机是否需要充电"""
    #     result = False
    #     if self.usage == Usage.NORMAL and \
    #             (self.task_type == TaskType.NO_TASK or self.task_type == TaskType.TO_RANDOM_POINT):
    #         # 非攻击用途无人机, 并且处于空闲状态
    #         for goods_obj in goods_objs:
    #             if self.uav.load_weight >= goods_obj.weight:
    #                 # 存在有能力运输但是电量不够的情况
    #                 enough = self.battery_enough(goods_obj, goods_obj.start, goods_obj.end)
    #                 result = result or not enough
    #
    #     return result

    def reset(self):
        """重置当前的Agent信息"""
        self.problem = RoutePlanProblem(
            map_range=self.map_info.map_range,
            h_low=self.map_info.h_low,
            h_high=self.map_info.h_low,
            obstacles=self.map_info.buildings)
        self.path = None  # a list of points(Coordinate obj)
        self.index = 1  # 当前路径节点的索引，第0个为起始点，不用包含在返回路径中
        self.task_type = TaskType.NO_TASK  # Agent状态：详见TaskType
        self.task_priority = TaskPriority.look_up(TaskType.NO_TASK)
        self.goods = None  # 已经分配的货物
        self.next_step = self.uav.loc  # 缓存下一步的坐标

    @staticmethod
    def vertical_path(x, y, start_h, end_h):
        """生成垂直路径"""
        if start_h < end_h:
            return [Coordinate(x, y, i)
                    for i in range(start_h, end_h + 1)]
        else:
            return [Coordinate(x, y, i)
                    for i in reversed(range(end_h, start_h + 1))]

    def _search(self, start, end, search_height, obstacles=None):
        """调用搜索算法进行路径搜索。"""

        if self.map_info.map_range.x > 0 and env.jpsp_finders \
                and search_height in env.jpsp_finders:
            # 大地图并且存在合法的JPSPlus对象，使用JPS算法搜索

            # print("UAV %d, JPS Plus search, height %d, " % (self.uav.no, search_height), end='')
            # jpsp_start_time = time.time()
            # jpsp_path = env.jpsp_finders[search_height].get_path(
            #     xy_to_loc(start.x, start.y), xy_to_loc(end.x, end.y))
            # print("time %s" % (time.time() - jpsp_start_time))

            print("UAV %d, JPSPlus search, height %d, " % (self.uav.no, search_height), end='')

            jpsp_start_time = time.time()
            jpsp_path = env.jpsp_finders[search_height].get_path(
                bridge.XYLoc(start.x, start.y), bridge.XYLoc(end.x, end.y))
            print("time %s" % (time.time() - jpsp_start_time))

            trans_start = time.time()
            search_result = bridge.to_coord_path(path=jpsp_path, height=search_height)
            print("Transform time %s" % (time.time() - trans_start))

        else:
            print("UAV %d, A-Star search, height %d, " % (self.uav.no, search_height), end='')
            self.problem.set_config(start=Coordinate(start.x, start.y, search_height),
                                    end=Coordinate(end.x, end.y, search_height),
                                    h_low=self.map_info.h_low,
                                    h_high=self.map_info.h_high,
                                    obstacles=obstacles,
                                    map_range=self.map_info.map_range)
            a_star_start_time = time.time()
            search_result = astar(self.problem, graph_search=True)
            print("time %s" % (time.time() - a_star_start_time))
            search_result = [c for _, c in search_result.path()]

        return search_result if search_result else []

    def plan(self, start: Coordinate, end: Coordinate, task_type,
             goods=None, obstacles=None):
        """根据地图规划路径"""
        if goods:
            self.goods = goods
        if not obstacles:
            obstacles = self.map_info.buildings
        self.task_type = task_type
        self.task_priority = TaskPriority.look_up(task_type)

        # 在二维平面内搜索路径，高度从h_low开始，如果搜索不到说明该平面内不可达，
        # 那么下次搜索的平面高度为：比当前search_height高的最小building高度 + 1
        # 搜索高度集合，building最后一个元素为top坐标
        height_list = [self.map_info.h_low] + [b[-1] + 1 for b in self.map_info.buildings
                                               if self.map_info.h_low < b[-1] < self.map_info.h_high]
        height_list = list(set(height_list))
        height_list.sort()
        search_result, search_height = None, 0
        fail_count = 0  # 搜索失败次数，超过3次，则在剩余的高度内随机挑选
        while not search_result and len(height_list) > 0:
            if fail_count < 3:
                search_height = height_list.pop(0)
            else:
                print('#' * 100)
                pop_idx = np.random.randint(0, len(height_list), size=1)
                search_height = height_list.pop(pop_idx)

            #################################################################
            # 路径搜索
            search_result = self._search(start, end, search_height, obstacles)
            #################################################################

            fail_count += 1 if not search_result else 0

        if search_result:
            # 产生三段路径：(start.x, start.y, start.z)->(start.x, start.y, h_low)->
            # (end.x, end.y, h_low)->(end.x, end.y, end.z)
            start_to_h_low = self.vertical_path(start.x, start.y, start.z, search_height)
            h_low_to_end = self.vertical_path(end.x, end.y, search_height, end.z)

            # self.path = [c for _, c in search_result.path()]
            self.path = start_to_h_low[:-1] + search_result + h_low_to_end[1:]  # 剔除衔接的重复结点
            self.index = 1
        else:
            raise ValueError('No path, uav_no: %d start: %s, end: %s' % (self.uav.no, start, end))

    def take_detour(self, encounter_agent, arranged_agents, mode=DetourMode.AUTO):
        """
        当前无人机选择避障，垂直方向移动一格，或者水平方向移动。
        :param arranged_agents: 包含无人机当前步和上一步信息，{no: (cur_step, next_step)}
        :return:
        """

        def _find_safe_detour(_arranged_agents, _mode=DetourMode.AUTO):
            if _mode != DetourMode.HORIZONTAL:
                # 优先选择垂直方向躲避, 躲避路径仍需考虑是否出现相遇和碰撞情况
                new_step = self.uav.loc + VERTICAL_DIRECTIONS[1]
                for a in _arranged_agents:
                    if new_step != a.next_step and \
                            not is_encounter(self.uav.loc, new_step, a.uav.loc, a.next_step):
                        # 如果无任务就不用返回原来的路径
                        print("\033[1;36mUAV %d, take a detour vertical.\033[0m" % self.uav.no)
                        return [new_step]  # if self.task_type == TaskType.NO_TASK else [new_step, self.uav.loc]
            if _mode != DetourMode.VERTICAL:
                # 其次选择水平方向躲避
                for di in HORIZONTAL_DIRECTIONS:
                    new_step = self.uav.loc + di
                    for a in _arranged_agents:
                        if new_step != a.next_step and \
                                not is_encounter(self.uav.loc, new_step, a.uav.loc, a.next_step):
                            # 如果无任务就不用返回原来的路径
                            print("\033[1;36mUAV %d, take a detour horizontal.\033[0m" % self.uav.no)
                            return [new_step]  # if self.task_type == TaskType.NO_TASK else [new_step, self.uav.loc]
            # return [self.uav.loc]

        if self.next_step != self.uav.loc:
            # 当前无人机产生了新的下一步，此时index递增了，回退一个
            self.index -= 1

        if self.uav.loc.z >= self.map_info.h_low:
            self.path = _find_safe_detour(arranged_agents) + self.path[self.index:]
            self.next_step = self.path[0]
            self.index = 1
        else:
            # self.path = _find_safe_detour(arranged_agents, _mode=DetourMode.VERTICAL) + self.path[self.index:]
            # self.next_step = self.path[0]
            # self.index = 1
            self.next_step = self.uav.loc

    def backspace(self):
        """返回上一步状态"""
        if self.next_step != self.uav.loc:
            self.index -= 1
        self.next_step = self.uav.loc

    def gen_next_step(self, step_info: StepInfo, goods_to_arrange_objs: list):
        """
        产生路径规划的下一步坐标
        :param step_info: 每一步服务器下发的信息
        :rtype: Coordinate
        """
        if not self.task_type == TaskType.TO_GOODS_START or \
                self.task_type == TaskType.TO_GOODS_END:
            # 任务和货物无关
            if self.task_type == TaskType.TO_CHARGE and \
                    self.uav.loc == self.map_info.parking:
                # 执行充电任务的无人机已经到达停机坪，重置状态，等待重新安排任务
                self.reset()
                print("\033[1;33mUAV %d, charge task finished, reset now.\033[0m"
                      % self.uav.no)
            else:
                if self.num_remain_steps <= 0:
                    # 不移动
                    self.next_step = self.uav.loc
                else:
                    self.next_step = self.path[self.index]
                    self.index += 1
        else:
            # 执行和货物有关的任务
            if self.num_remain_steps > 0:
                # 未到达终点
                self.next_step = self.path[self.index]
                self.index += 1
            else:
                # 到达目的地
                if self.uav.loc == self.goods.start:
                    # 到达货物出现地点，把无人机货物编号设置为good.no取货，并规划到目的地的路径
                    self.uav.goods_no = self.goods.no
                    self.plan(self.uav.loc, self.goods.end, task_type=TaskType.TO_GOODS_END)
                    self.next_step = self.uav.loc
                    # res = self.path[self.index]
                    # self.index += 1
                elif self.uav.loc == self.goods.end:
                    # 货物送到目的地
                    self.reset()  # 此时无人机算空闲, 直接重置状态

                    # 飞机垂直上升到(x, y, h_low)
                    self.path = self.vertical_path(
                        self.uav.loc.x, self.uav.loc.y, self.uav.loc.z, self.map_info.h_low)
                    self.next_step = self.path[self.index]
                    self.index += 1
                else:
                    # 有可能出错了，暂时原地不动
                    self.next_step = self.uav.loc


if __name__ == '__main__':

    _a = Coordinate(1, 0, 0)
    _b = Coordinate(0, 0, 0)

    for di in HORIZONTAL_DIRECTIONS:
        _next_a = _a + di
        for dj in HORIZONTAL_DIRECTIONS:
            _next_b = _b + dj
            res = is_encounter(_a, _next_a, _b, _next_b)
            if res:
                print(_next_a, _next_b, res)
