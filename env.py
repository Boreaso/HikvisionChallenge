import queue


def singleton(cls):
    instances = {}

    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper


@singleton
class Env(object):
    def __init__(self):
        self.attackerToEnemy = {}  # attacker id : enemy uav id

        self.goodsToTrack = set()

        self.attackerToGood = {}

        # 需要攻击的货物
        self.goods_to_attack = {}

        # 指定高度的JPS对象字典，Key为高度，Value为对应的JPS对象
        self.jpsp_finders = {}

        # Agent对象字典，Key为UAV的no，Value为Agent对象
        self.agents = {}

        # 平面坐标处于Parking的无人机
        self.uav_on_parking_xy_set = set()

        # 已到达parking上方的需要充电的无人机
        self.uav_charge_approaching_parking = set()

        # 处于基地垂直方向的无人机
        self.uav_leaving_parking = set()

        # 有敌方无人机处于基地上空
        self.enemy_above_parking = set()


env = Env()
