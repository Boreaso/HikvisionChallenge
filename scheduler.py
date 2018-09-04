import multiprocessing
import sys

import numpy as np

from env import env
from model import Coordinate, Goods, GoodsState, MapInfo, StepInfo, UAV, UAVStatus
from route_plan import Agent, DIST_ESTIMATE_RATE, TaskType, Usage, diagonal_dis_3d, is_encounter, manhattan_dis_3d, \
    manhattan_distance


def gen_random_points(num_points, map_info: MapInfo):
    """
    生成当前地图中的合法的随机点，把空闲无人机分散到各个角落
    :param num_points: 所需生成的坐标点数量
    :param map_info: 当前地图信息
    :return:
    """
    low, high = 0, map_info.map_range.x
    xy = np.random.randint(low=low, high=high, size=(2, num_points))  # 生成随机坐标
    points = [Coordinate(x=x, y=y, z=map_info.h_low) for x, y in zip(xy[0, :], xy[1, :])]

    # 对于不合法的点(和障碍物重叠)，重新生成
    for i in range(len(points)):
        while points[i].is_overlap(map_info.buildings):
            x, y = np.random.randint(low=0, high=map_info.map_range.x, size=2)
            points[i] = Coordinate(x, y, map_info.h_low)

    return points


def validate_data(map_info: MapInfo, step_info: StepInfo, goods_to_carry: set):
    # 删除不可用的Agent, 添加新增的Agent，Agent状态检查
    for uav in step_info.uav_we.values():
        if uav.status == UAVStatus.CRASHED:
            # 无人机坠毁，不再继续受控制
            if uav.no in env.agents:
                env.agents.pop(uav.no)
            continue

        if uav.no not in env.agents:
            # 新增的无人机
            env.agents[uav.no] = Agent(uav, map_info)

        if env.agents[uav.no].task_type == TaskType.TO_GOODS_START and \
                env.agents[uav.no].goods.no not in goods_to_carry:
            # 已规划的货物不可搬运，终止任务（重置Agent）
            env.agents[uav.no].reset()

        # 更新UAV信息
        env.agents[uav.no].update_uav_info(uav)

    # 移除已经消失的货物
    for goods_no in list(env.goods_to_attack.keys()):
        if goods_no not in step_info.goods:
            if env.goods_to_attack[goods_no] > 0:
                # 任务重置
                agent = env.agents[env.goods_to_attack[goods_no]]
                agent.reset()
            env.goods_to_attack.pop(goods_no)
        elif env.goods_to_attack[goods_no] not in step_info.uav_we:
            # 无人机被撞毁了
            env.goods_to_attack[goods_no] = -1

    # 检查敌方无人机是否攻占基地上空
    # for enemy in step_info.uav_enemy.values():
    #     if enemy.no not in env.enemy_above_parking and \
    #             enemy.status == UAVStatus.NORMAL and \
    #             enemy.loc.xy_equal(map_info.parking):
    #         # 存在敌机处于基地上空
    #         env.enemy_above_parking.add(enemy.no)
    #         print("\033[1;33mEnemy %d, enemy_above_parking added.\033[0m"
    #               % enemy.uav.no)
    #     elif enemy.no in env.enemy_above_parking and \
    #             enemy.status == UAVStatus.CRASHED:
    #         # 敌机已被摧毁
    #         env.enemy_above_parking.remove(enemy.no)
    #         print("\033[1;33mEnemy %d, enemy_above_parking removed.\033[0m"
    #               % enemy.uav.no)


def arrange_uav(map_info: MapInfo, step_info: StepInfo, goods_to_arrange: set):
    # 按货物价值由大到小排序
    goods_objs = sorted([step_info.goods[no] for no in goods_to_arrange],
                        key=lambda x: -x.value)

    def _estimate_goods_earnings(agent: Agent, goods: Goods):
        dist = diagonal_dis_3d(agent.uav.loc, goods_obj.start, map_info.h_low)
        dist = int(dist * DIST_ESTIMATE_RATE)
        if goods_obj.weight <= agent.uav.load_weight and \
                dist < goods_obj.left_time and \
                agent.battery_enough(goods_obj.weight, goods_obj.start, goods_obj.end):
            # 可以搬运
            if goods.state == GoodsState.CARRIED:
                # 货物被捡起
                if goods.no not in env.goods_to_attack:
                    env.goods_to_attack[goods.no] = -1
                return 0

            for enemy in step_info.uav_enemy.values():
                if enemy.loc.xy_equal(goods.start):
                    if goods.no not in env.goods_to_attack:
                        # 该货物已经无法获取
                        env.goods_to_attack[goods.no] = -1
                    return 0
            return agent.estimate_earnings(goods)
        else:
            return 0

    for agent in env.agents.values():
        if agent.task_type == TaskType.TO_GOODS_END or \
                agent.task_type == TaskType.ATTACK_ENEMY:
            # 正在运货的和攻击的无人机不安排
            continue

        most_valuable_goods, max_earnings = None, 0
        for goods_no in goods_to_arrange:
            goods_obj = step_info.goods[goods_no]
            earnings = _estimate_goods_earnings(agent, goods_obj)
            if earnings > max_earnings:
                most_valuable_goods, max_earnings = goods_obj, earnings

        if most_valuable_goods is not None:
            # 已经分配了无人机
            goods_to_arrange.remove(most_valuable_goods.no)

        if agent.task_type == TaskType.TO_GOODS_START and \
                agent.goods.no == most_valuable_goods.no:
            # 运货任务不变
            continue

        # 重新规划任务目标
        if agent.task_type == TaskType.TO_GOODS_START:
            print("\033[1;31mUAV %d, task goods changed: %d -> %d.\033[0m"
                  % (agent.uav.no, agent.goods.no, most_valuable_goods.no))
        else:
            print("\033[1;31mUAV %d, new task goods arranged: %d.\033[0m"
                  % (agent.uav.no, most_valuable_goods.no))

        agent.plan(agent.uav.loc, most_valuable_goods.start,
                   task_type=TaskType.TO_GOODS_START)

    return {}


def better_uav(map_info: MapInfo, step_info: StepInfo,
               goods_to_arrange: set):
    # 按货物价值由大到小排序
    goods_objs = sorted([step_info.goods[no] for no in goods_to_arrange],
                        key=lambda x: -x.value)
    for agent in env.agents.values():
        if agent.task_type == TaskType.TO_GOODS_START:
            for goods_obj in goods_objs:
                dist = diagonal_dis_3d(agent.uav.loc, goods_obj.start, map_info.h_low)
                dist = int(dist * DIST_ESTIMATE_RATE)
                if goods_obj.weight <= agent.uav.load_weight and \
                        dist < goods_obj.left_time and \
                        agent.battery_enough(goods_obj.weight, goods_obj.start, goods_obj.end):
                    # 可以搬运
                    if goods_obj.value > agent.goods.value and dist <= agent.num_remain_steps and \
                            agent.battery_enough(goods_obj.weight, goods_obj.start, goods_obj.end):
                        print("\033[1;31mUAV %d, path replan.\033[0m" % agent.uav.no)
                        agent.plan(start=agent.uav.loc,
                                   end=goods_obj.start,
                                   goods=goods_obj,
                                   task_type=TaskType.TO_GOODS_START)


def attack_enemy(map_info: MapInfo, step_info: StepInfo):
    """
    主动攻击敌方无人机，主动攻击的己方无人机需要满足两个如下条件：
    1.无任务在身。2.价值最小或者比攻击的敌方无人机价值小
    :param map_info: 地图信息：障碍物，地图大小，停机坪位置。。。
    :param step_info: 当前赛场信息，包括己方无人机信息，敌方无人机信息，货物信息等等。
    :return: 不需要返回，直接对Agent进行操作
    """
    print('attack enemy')
    _threshold = manhattan_distance(Coordinate(0, 0, 0), map_info.map_range) / 2

    print('threshold', _threshold)

    def _near(coord1, coord2, threshold):
        """ simplify, decide if attacker is near end """
        return manhattan_distance(coord1, coord2) <= threshold

    def _done(enemy_id):  # 需要考虑雾区
        uav = step_info.uav_enemy[enemy_id]
        return uav.status == UAVStatus.CRASHED or uav.goods_no == -1

    def _valuable(enemy_id):
        # enemy should carry good, and good lifetime should be valid
        uav = step_info.uav_enemy[enemy_id]
        if uav.goods_no == -1:
            return False
        # return True
        good = step_info.goods[uav.goods_no]
        return good.left_time > manhattan_dis_3d(uav.loc, good.end, map_info.h_low)

    def _earlier(our_loc, enemy_loc, end):
        x, y = end.x, end.y
        h_low = map_info.h_low
        return manhattan_dis_3d(our_loc, Coordinate(x, y, h_low), h_low) < \
               manhattan_dis_3d(enemy_loc, Coordinate(x, y, 0), h_low)

    # attack ends  -> idle
    for agent in env.agents.values():
        if agent.task_type == TaskType.ATTACK_ENEMY:
            enemy_id = env.attackerToEnemy.get(agent.uav.no)
            if enemy_id and _done(enemy_id):
                env.attackerToEnemy.pop(agent.uav.no)
                agent.task_type = TaskType.NO_TASK
                print('ATTACK -> NO_TASK')

    # idle -> attack    do assign & plan
    for agent in env.agents.values():
        if agent.task_type == TaskType.NO_TASK or agent.task_type == TaskType.TO_RANDOM_POINT:
            for enemy_uav in step_info.uav_enemy.values():
                _enemy_id = enemy_uav.no
                if _enemy_id not in env.attackerToEnemy.values() \
                        and enemy_uav.status == UAVStatus.NORMAL \
                        and _valuable(_enemy_id):  # enemy 没有被assign && 可见 && 有价值
                    print('In here')
                    goods_no = step_info.uav_enemy[_enemy_id].goods_no
                    x, y = step_info.goods[goods_no].end.x, step_info.goods[goods_no].end.y
                    _end = Coordinate(x, y, map_info.h_low)
                    # if _near(agent.uav.loc, _end, threshold):
                    if _near(agent.uav.loc, _end, _threshold) and _earlier(agent.uav.loc, enemy_uav.loc, _end):
                        print('NO_TASK->ATTACK')
                        env.attackerToEnemy[agent.uav.no] = _enemy_id
                        agent.plan(agent.uav.loc, _end, task_type=TaskType.ATTACK_ENEMY)


def attack_enemy2(map_info: MapInfo, step_info: StepInfo):
    arranged_goods_list = [a.goods.no for a in env.agents.values() if a.goods]

    for goods_no in env.goods_to_attack:
        if env.goods_to_attack[goods_no] < 0:
            # 寻找可以攻击的无人机
            for agent in env.agents.values():
                max_earnings_agent, max_earnings = None, sys.maxsize
                if agent.task_type == TaskType.NO_TASK or \
                        agent.task_type == TaskType.TO_RANDOM_POINT or \
                        agent.usage == Usage.ATTACK:
                    good_obj = step_info.goods[goods_no]
                    dist_to_ = diagonal_dis_3d(agent.uav.loc, good_obj.end, map_info.h_low)


def avoid_enemy(map_info: MapInfo, step_info: StepInfo):
    """
    规避敌方无人机，防止己方高价值无人机被撞毁。(需要考虑所有己方无人机，包括有任务和没任务的)
    :param map_info: 地图信息：障碍物，地图大小，停机坪位置。。。
    :param step_info: 当前赛场信息，包括己方无人机信息，敌方无人机信息，货物信息等等。
    :return: 不需要返回，直接对Planer进行操作
    """
    pass


def avoid_self(map_info: MapInfo, step_info: StepInfo):
    """
    规避己方无人机，保证产生的下一步路径符合赛题规范。
    :param map_info: 地图信息：障碍物，地图大小，停机坪位置。。。
    :param step_info: 当前赛场信息，包括己方无人机信息，敌方无人机信息，货物信息等等。
    :return: 不需要返回，直接对Planer进行操作
    """

    def _select(p_a: Agent, p_b: Agent):
        if p_a.task_priority == p_b.task_priority and \
                p_a.task_type == TaskType.TO_GOODS_START:
            if p_a.goods.value > p_b.goods.value:
                return p_b
            else:
                return p_a

        return p_a if p_a.task_priority > p_b.task_priority else p_b

    agent_list = list(env.agents.values())
    for i in range(len(agent_list)):
        # 检查坐标合法性，避免碰撞
        p_i = agent_list[i]
        for j in range(i + 1, len(agent_list)):
            p_j = agent_list[j]
            if p_i.next_step != map_info.parking and p_j.next_step != map_info.parking:
                # if p_i.next_step == p_j.next_step:
                #     # 下一步规划到了同一个路径，无任务的，或任务价值小的等待
                #     tmp_p = _select(p_i, p_j)
                #     tmp_p.backspace()
                if is_encounter(p_i.uav.loc, p_i.next_step, p_j.uav.loc, p_j.next_step):
                    # 出现相遇的情况
                    tmp_p = _select(p_i, p_j)
                    tmp_p.take_detour(p_i if tmp_p != p_i else p_j, agent_list)


def purchase_uav(map_info: MapInfo, step_info: StepInfo,
                 over_weight_stats: dict):
    """
    购买无人机
    :param over_weight_stats: 我方无人机运力统计
    :param map_info: 地图信息：障碍物，地图大小，停机坪位置。。。
    :param step_info: 当前赛场信息，包括己方无人机信息，敌方无人机信息，货物信息等等。
    :return: 所需购买无人机的列表
    """
    # 购买无人机, 如果出现当前不能运输的物品，则优先购买大运力无人机，
    # 其他全部购买最小价值的飞机
    # result = []
    # for weight, buy_num in over_weight_stats.items():
    #     # 查找满足指定重量的无人机
    #     price_obj = None
    #     # 查找满足指定重量的无人机, map_info.uav_price已经按weight排序
    #     for price in map_info.uav_price.values():
    #         if step_info.we_value >= price.value and price.load_weight >= weight:
    #             price_obj = price
    #     if price_obj:
    #         for _ in range(buy_num):
    #             if step_info.we_value >= price_obj.value:
    #                 result.append({"purchase": price_obj.uav_type})
    #                 step_info.we_value -= price_obj.value
    #
    # min_price_obj = None
    # for price in map_info.uav_price.values():
    #     if not min_price_obj or price.value < min_price_obj.value:
    #         min_price_obj = price
    # if min_price_obj and step_info.we_value >= min_price_obj.value:
    #     result.append({"purchase": min_price_obj.uav_type})
    #     step_info.we_value -= min_price_obj.value
    #
    # buy_idx = np.random.randint(0, len(map_info.uav_price), 1)
    # for i, price in enumerate(map_info.uav_price.values()):
    #     if buy_idx == i and step_info.we_value > price.value:
    #         result.append({"purchase": price.uav_type})
    #         step_info.we_value -= price.value
    #         break
    # result = []
    # price_list = list(map_info.uav_price.values())
    # # np.random.shuffle(price_list)
    # for price in price_list:
    #     if step_info.we_value > price.value:
    #         result.append({"purchase": price.uav_type})
    #         step_info.we_value -= price.value

    result = []
    price_list = list(map_info.uav_price.values())
    # np.random.shuffle(price_list)
    min_price = price_list[0]
    for price in price_list:
        if price.value < min_price.value:
            min_price = price
    if step_info.we_value > min_price.value:
        result.append({"purchase": min_price.uav_type})
        step_info.we_value -= min_price.value

    return result


def schedule(map_info: MapInfo, step_info: StepInfo,
             mp_pool: multiprocessing.Pool):
    """
    主调度程序，接收地图信息，服务器下达的对战信息以及当前己方无人机的Planer，
    返回StepCommand对象的json。
    :param mp_pool: 进程池对象
    :param map_info: 地图信息
    :param step_info: 接收服务器发送的对战信息。
    :return: 计算后返回给服务器的下一步指令信息，即StepCommand的json。
    """
    if not step_info:
        # 此时不能移动无人机，返回无人机初始位置
        uav_info = [a.uav.to_info_dict() for a in env.agents.values()]
        return uav_info, []

    # 待搬运的货物
    goods_to_carry = set([g.no for g in step_info.goods.values() if g.state == 0])

    # 合法化当前数据
    validate_data(map_info, step_info, goods_to_carry)

    # 已经分配了无人机的货物
    # goods_arranged = set([a.goods.no for a in env.agents.values() if
    #                       a.task_type == TaskType.TO_GOODS_START])
    # 待分配无人机的货物
    # goods_to_arrange = goods_to_carry - goods_arranged

    # 分配无人机
    over_weight_stats = arrange_uav(map_info, step_info, goods_to_carry)

    # 已有任务的无人机选择更有价值的货物
    # better_uav(map_info, step_info, goods_to_arrange)

    # 把无任务的无人机随机分散到各个角落
    if not env.uav_charge_approaching_parking:
        # 基地上空没有正在返回充电的无人机
        idle_agents = [a for a in env.agents.values() if
                       a.task_type == TaskType.NO_TASK]
        points = gen_random_points(len(idle_agents), map_info)
        for i, agent in enumerate(idle_agents):
            if agent.usage == Usage.ATTACK or agent.full_charged:
                # 如果攻击型无人机则不考虑电量，运货的无人机需要考虑电量
                agent.plan(start=agent.uav.loc, end=points[i],
                           task_type=TaskType.TO_RANDOM_POINT)

    # 主动攻击敌方无人机
    try:
        attack_enemy(map_info, step_info)
    except Exception:
        pass

    # 产生下一步的无人机坐标
    goods_to_arrange_objs = sorted([step_info.goods[no] for no in goods_to_arrange],
                                   key=lambda x: -x.value)
    for a in env.agents.values():
        a.gen_next_step(step_info, goods_to_arrange_objs)

    # 规避敌方无人机
    avoid_enemy(map_info, step_info)

    # 规避己方无人机
    avoid_self(map_info, step_info)

    # 准备返回给服务器的无人机信息
    uav_info = []
    for a in env.agents.values():
        # 更新电量信息
        a.update_electricity(step_info.goods)

        # 构造返回消息
        tmp_uav = UAV(a.uav.no, a.next_step.x, a.next_step.y, a.next_step.z, a.uav.goods_no,
                      remain_electricity=a.uav.remain_electricity)

        uav_info.append(tmp_uav.to_info_dict())

    # 购买无人机
    purchase_info = purchase_uav(map_info, step_info, over_weight_stats)

    return uav_info, purchase_info
