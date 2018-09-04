import json


class Coordinate:
    """坐标运算类"""

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.x == other.x and self.y == other.y and self.z == other.z

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        return self.__class__(self.x, self.y, self.z)

    def __add__(self, other):
        if isinstance(other, self.__class__):
            x = self.x + other.x
            y = self.y + other.y
            z = self.z + other.z
        elif isinstance(other, tuple) and len(other) == 3:
            x = self.x + other[0]
            y = self.y + other[1]
            z = self.z + other[2]
        else:
            x = y = z = -1
        return self.__class__(x, y, z)

    def __sub__(self, other):
        if isinstance(other, self.__class__):
            x = self.x - other.x
            y = self.y - other.y
            z = self.z - other.z
        elif isinstance(other, tuple) and len(other) == 3:
            x = self.x - other[0]
            y = self.y - other[1]
            z = self.z - other[2]
        else:
            x = y = z = -1
        return self.__class__(x, y, z)

    def __hash__(self):
        return hash('%d%d%d' % (self.x, self.y, self.z))

    def __str__(self):
        return "(%d, %d, %d)" % (self.x, self.y, self.z)

    def xy_equal(self, other):
        """是否处于同一平面坐标"""
        return self.x == other.x and self.y == other.y

    def is_valid(self, map_x, map_y, map_z):
        """检查是否越界"""
        return 0 <= self.x <= map_x and \
               0 <= self.y <= map_y and \
               0 <= self.z <= map_z

    def is_overlap(self, spaces):
        """
        判断坐标是否在和space空间重叠
        :param spaces: [(x1, y1, x2, y2, z1, z2), ...]
        x1,y1表示建立体区域的水平起始坐标， x2, y2表示水平终止坐标（x2=x1+l, y2=y1+w），
        z1,z2分别为垂直起止坐标
        :return: True or False
        """
        for space in spaces:
            x1, y1, x2, y2, z1, z2 = space
            step = x1 <= self.x <= x2 and \
                   y1 <= self.y <= y2 and \
                   z1 <= self.z <= z2
            if step:
                return True
        return False


# class DictObj:
#     def __init__(self, dic):
#         self.dic = dic
#
#     def __setattr__(self, name, value):
#         if name == 'dic':
#             object.__setattr__(self, name, value)
#             return
#
#         self.dic[name] = value
#
#     def __getattr__(self, name):
#         if name not in self.dic:
#             return None
#         v = self.dic[name]
#         if isinstance(v, dict):
#             return DictObj(v)
#         if isinstance(v, list):
#             return [DictObj(i) for i in v]
#         elif name in self.dic:
#             return self.dic[name]
#
#     def __getitem__(self, name):
#         if name in self.dic:
#             return self.dic[name]
#         else:
#             return None


class UAVPrice:
    """无人机价格信息"""

    def __init__(self, uav_type, load_weight, value, capacity, charge):
        self.uav_type = uav_type
        self.load_weight = load_weight
        self.value = value

        # 复赛新增字段
        self.capacity = capacity
        self.charge = charge

    @staticmethod
    def from_dict(data_dict):
        return UAVPrice(data_dict['type'],
                        data_dict['load_weight'],
                        data_dict['value'],
                        data_dict['capacity'],
                        data_dict['charge'])


class UAVStatus:
    NORMAL = 0
    CRASHED = 1
    IN_FOG = 2
    CHARGING = 3


class UAV:
    """无人机类"""

    def __init__(self, no, x, y, z, goods_no=-1, uav_type=None, status=UAVStatus.NORMAL,
                 remain_electricity=None, price=None, load_weight=None,
                 capacity=None, charge=None):
        """
        :param no: 无人机编号
        :param x: x坐标
        :param y: y坐标
        :param z: z坐标
        :param goods_no: 货物编号， 通过Goods确定具体信息
        :param uav_type: 无人机类型， 通过UAVPrice确定具体信息
        :param status: 无人机状态 0表示正常， 1表示坠毁， 2表示处于雾区， 3表示正在充电
        :param price: 无人机价格
        :param load_weight: 载重
        """
        self.no = no
        self.loc = Coordinate(x, y, z)
        self.goods_no = goods_no
        self.uav_type = uav_type
        self.status = status
        self.price = price
        self.load_weight = load_weight
        self.capacity = capacity
        self.charge = charge

        # 复赛新增字段
        self.remain_electricity = remain_electricity

    def assign(self, other):
        self.no = other.no
        self.loc = other.loc
        self.goods_no = other.goods_no
        self.uav_type = other.uav_type
        self.status = other.status
        self.price = other.price
        self.load_weight = other.load_weight
        self.capacity = other.capacity
        self.charge = other.charge

    def to_info_dict(self):
        return {'no': self.no,
                'x': self.loc.x,
                'y': self.loc.y,
                'z': self.loc.z,
                'goods_no': self.goods_no,
                'remain_electricity': self.remain_electricity}

    @staticmethod
    def from_dict(data_dict, uav_price: UAVPrice = None):
        return UAV(data_dict["no"],
                   data_dict["x"],
                   data_dict["y"],
                   data_dict["z"],
                   data_dict["goods_no"],
                   data_dict["type"],
                   data_dict["status"],
                   data_dict["remain_electricity"],
                   uav_price.value if uav_price else None,
                   uav_price.load_weight if uav_price else None,
                   uav_price.capacity if uav_price else None,
                   uav_price.charge if uav_price else None)


class GoodsState:
    NORMAL = 0
    CARRIED = 1


class Goods:
    """货物类"""

    def __init__(self, no, start_x, start_y, end_x, end_y, weight, value,
                 start_time, remain_time, left_time, state):
        """
        :param start_x:  货物出现的地面x坐标
        :param start_y: 货物出现的地面y坐标
        :param end_x: 货物需要运送到的地面x坐标
        :param end_y: 货物需要运送到的地面y坐标
        :param weight: 货物的重量
        :param value: 运送到后货物的价值
        :param start_time: 货物的持续时间
        :param left_time: 离货物消失的剩余时间
        :param remain_time: 货物剩余的时间
        :param state: state为0表示货物正常且可以被拾起,state为1表示已经被无人机拾起，
                      已经消失或送到的货物会在列表中被删除
        """
        self.no = no
        self.start = Coordinate(start_x, start_y, 0)
        self.end = Coordinate(end_x, end_y, 0)
        self.weight = weight
        self.value = value
        self.start_time = start_time
        self.remain_time = remain_time
        self.left_time = left_time
        self.state = state

    @staticmethod
    def from_dict(data_dict):
        return Goods(data_dict["no"],
                     data_dict["start_x"],
                     data_dict["start_y"],
                     data_dict["end_x"],
                     data_dict["end_y"],
                     data_dict["weight"],
                     data_dict["value"],
                     data_dict["start_time"],
                     data_dict["remain_time"],
                     data_dict["left_time"],
                     data_dict["status"])


class MapInfo:
    """全局静态信息"""

    def __init__(self, map_range: Coordinate, parking: Coordinate, h_low: int, h_high: int,
                 buildings: list, fogs: list, init_uav: dict, uav_price: dict):
        """
        :param map_range: 地图范围 (x,y,z)
        :param parking: 停机坪信息 (x,y,z)
        :param h_low: "飞行最低高度": 固定值
        :param h_high: "飞行最高高度": 固定值
        :param buildings:[(x1, y1, x2, y2, z1, z2), ...]
        x1,y1表示建立体区域的水平起始坐标， x2, y2表示水平终止坐标（x2=x1+l, y2=y1+w），
        z1,z2分别为垂直起止坐标
        :param fogs: [(x1, y1, x2, y2, z1, z2), ...]
        x1,y1表示建立体区域的水平起始坐标， x2, y2表示水平终止坐标（x2=x1+l, y2=y1+w），
        z1,z2分别为垂直起止坐标
        :param init_uav: "一开始停机坪无人机信息": "固定值，整个比赛过程中不变，无人机个数根据地图而不同，
        无人机信息包括 编号和最大载重量，编号单方唯一"
        :param uav_price:"无人机价格表": "固定值，整个比赛过程中不变，no表示无人机购买编号，价格表根据载重不同，
        价值也不同，初始化的无人机中的载重必定在这个价格表中，方便统计最后价值"
        """
        self.map_range = map_range
        self.parking = parking
        self.h_low = h_low
        self.h_high = h_high
        self.buildings = buildings
        self.fogs = fogs
        self.init_uav = init_uav
        self.uav_price = {k: v for k, v in sorted(uav_price.items(), key=lambda x: -x[1].load_weight)}
        self.price_order = [k for k in self.uav_price.keys()][::-1]

    @staticmethod
    def from_dict(data_dict):
        return MapInfo(
            map_range=Coordinate(*[data_dict['map'][k] - 1 for k in data_dict['map']]),
            parking=Coordinate(data_dict['parking']['x'], data_dict['parking']['y'], 0),
            h_low=data_dict['h_low'],
            h_high=data_dict['h_high'],
            buildings=[(f['x'], f['y'], f['x'] + f['l'] - 1, f['y'] + f['w'] - 1, 0, f['h'])
                       for f in data_dict['building']],
            fogs=[(f['x'], f['y'], f['x'] + f['l'] - 1, f['y'] + f['w'] - 1, f['b'], f['t'])
                  for f in data_dict['fog']],
            init_uav={uav['no']: UAV.from_dict(uav) for uav in data_dict['init_UAV']},
            uav_price={a['type']: UAVPrice.from_dict(a) for a in data_dict['UAV_price']})


class StepInfo:
    """服务器每一步返回的实时对战信息"""

    def __init__(self, token: str, notice: str, match_status: int,
                 time: int, uav_we: dict, we_value: int, uav_enemy: dict,
                 enemy_value: int, goods: dict):
        self.token = token
        self.notice = notice
        self.match_status = match_status
        self.time = time
        self.uav_we = uav_we
        self.we_value = we_value
        self.uav_enemy = uav_enemy
        self.enemy_value = enemy_value
        self.goods = goods

    @staticmethod
    def from_dict(data_dict, map_info: MapInfo):
        return StepInfo(
            token=data_dict['token'],
            notice=data_dict['notice'],
            match_status=data_dict['match_status'],
            time=data_dict['time'],
            uav_we={uav['no']: UAV.from_dict(uav, map_info.uav_price[uav['type']])
                    for uav in data_dict['UAV_we']},
            we_value=data_dict['we_value'],
            uav_enemy={uav['no']: UAV.from_dict(uav, map_info.uav_price[uav['type']])
                       for uav in data_dict['UAV_enemy']},
            enemy_value=data_dict['enemy_value'],
            goods={g['no']: Goods.from_dict(g) for g in data_dict['goods']})


class StepCommand:
    """每一步发送给服务器的指令，包括无人机信息，和购买请求等."""

    def __init__(self, token: str, uav_info: list, purchase_uav: list = None):
        """
        :param token: 唯一token
        :param uav_info: UAV对象列表
        :param purchase_uav: ['F1', 'F2', ...]
        字符串列表，表示购买的型号， None表示不购买
        """
        self.token = token
        self.uav_info = uav_info
        self.purchase_uav = purchase_uav

    def update(self, uav_info, purchase_uav=None):
        self.uav_info = uav_info
        self.purchase_uav = purchase_uav

    def to_json(self):
        json_dict = {"token": self.token,
                     "action": "flyPlane",
                     "UAV_info": [uav.to_info_dict() for uav in self.uav_info]}
        if self.purchase_uav:
            json_dict['purchase_UAV'] = [{'purchase': t} for t in self.purchase_uav]
        return json.dumps(json_dict)


if __name__ == '__main__':
    # json_obj = json.load(open('data/map_info.json'))
    # start = time.time()
    # info = MapInfo.from_dict(json_obj)
    # end = time.time()
    # print('Time: %s' % (end - start))

    c1 = Coordinate(1, 1, 1)
    c2 = Coordinate(2, 2, 2)
    c_list = [c1, c2]

    print(Coordinate(1, 1, 1) in c_list)
