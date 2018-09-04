import json
import multiprocessing
import socket
import sys
import time

from env import env
# from jpsp_boost import libjpsp
from jpsp_c_api import jpsp_bridge as bridge
from model import MapInfo, StepInfo, UAV, UAVStatus
from route_plan import Agent
from scheduler import schedule


# 从服务器接收一段字符串, 转化成字典的形式
def recv_judger_data(h_socket):
    n_ret = -1
    len_json = int(h_socket.recv(8))

    rcved, message = 0, bytes()
    while rcved != len_json:
        t = h_socket.recv(1024 * 4)
        rcved += len(t)
        message += t

    str_json = message.decode()
    print("Recv: ", str_json)

    if len(str_json) == len_json:
        n_ret = 0
    json_str = json.loads(str_json)

    return n_ret, json_str


# 接收一个字典,将其转换成json文件,并计算大小,发送至服务器
def send_judger_data(h_socket, dict_send):
    str_json = json.dumps(dict_send)
    len_json = str(len(str_json)).zfill(8)
    str_all = len_json + str_json
    print("Send: ", str_all)
    ret = h_socket.sendall(str_all.encode())
    if ret is None:
        ret = 0
    print('sendall', ret)
    return ret


# 用户自定义函数, 返回字典fly_plane, 需要包括 "UAV_info", "purchase_UAV" 两个key.
def algorithm_calculation_fun(map_info: MapInfo, step_info: StepInfo,
                              mp_pool: multiprocessing.Pool):
    """
    算法主函数，接收服务器下达的对战信息，返回StepCommand对象的json。
    :param mp_pool:
    :param map_info: 地图信息
    :param step_info: 接收服务器发送的对战信息。
    :return: 计算后返回给服务器的下一步指令信息，即StepCommand的json。
    """
    return schedule(map_info, step_info, mp_pool)


def main(sz_ip, n_port, sz_token, mp_pool: multiprocessing.Pool = None):
    print("server ip %s, port %d, token %s\n" % (sz_ip, n_port, sz_token))

    # 开始连接服务器
    h_socket = socket.socket()

    h_socket.connect((sz_ip, n_port))

    # 接受数据。连接成功后，Judger会返回一条消息：
    n_ret, _ = recv_judger_data(h_socket)
    if n_ret != 0:
        return n_ret

    # 生成表明身份的json
    token = {'token': sz_token, 'action': "sendtoken"}

    # 选手向裁判服务器表明身份(Player -> Judger)
    n_ret = send_judger_data(h_socket, token)
    if n_ret != 0:
        return n_ret

    # 身份验证结果(Judger -> Player), 返回字典message
    n_ret, message = recv_judger_data(h_socket)
    if n_ret != 0:
        return n_ret

    if message["result"] != 0:
        print("token check error\n")
        return -1

    # 选手向裁判服务器表明自己已准备就绪(Player -> Judger)
    st_ready = {'token': sz_token, 'action': "ready"}

    n_ret = send_judger_data(h_socket, st_ready)
    if n_ret != 0:
        return n_ret

    # 对战开始通知(Judger -> Player)
    n_ret, message = recv_judger_data(h_socket)
    if n_ret != 0:
        return n_ret

    # 初始化地图信息
    pst_map_info = message["map"]

    # 初始化比赛状态信息
    pst_match_status = {"time": 0}

    # 初始化地图对象
    map_info = MapInfo.from_dict(pst_map_info)

    # 初始化JPSPlus对象
    # height_list = [map_info.h_low] + [
    #     b[-1] + 1 for b in map_info.buildings if map_info.h_low < b[-1] < map_info.h_high]
    # jpsp_init_start_time = time.time()
    # for height in range(map_info.h_high + 1):
    #     map_w, map_h = map_info.map_range.x + 1, map_info.map_range.y + 1
    #     map_data = make_map_data(map_w, map_h, map_info.buildings, height)
    #     env.jpsp_finders[height] = libjpsp.JPSPWrapper(map_data, map_w, map_h)
    #     env.jpsp_finders[height].preprocess()
    # print("JPS Plus finder init finished, time %s" % (time.time() - jpsp_init_start_time))

    height_list = [map_info.h_low] + [
        b[-1] + 1 for b in map_info.buildings if map_info.h_low < b[-1] < map_info.h_high]
    jpsp_init_start_time = time.time()
    for height in set(height_list):
        map_w, map_h = map_info.map_range.x + 1, map_info.map_range.y + 1
        env.jpsp_finders[height] = bridge.JPSPlus(
            map_w, map_h, buildings=map_info.buildings, search_height=height)
        env.jpsp_finders[height].preprocess()
    print("JPS Plus finder init finished, time %s" % (time.time() - jpsp_init_start_time))

    # 初始化飞机Planer
    # agents = {}
    for uav_dic in pst_map_info["init_UAV"]:
        uav = UAV.from_dict(uav_dic, map_info.uav_price[uav_dic['type']])
        env.agents[uav.no] = Agent(uav=uav, map_info=map_info)

    # 每一步的飞行计划
    fly_plane_send = {"token": sz_token, "action": "flyPlane"}

    time_out_count = 0
    time_out_stats = {}
    time_span_list = []
    # 根据服务器指令，不停的接受发送数据
    while True:
        step_time_start = time.time()

        # 进行当前时刻的数据计算, 填充飞行计划，注意：1时刻不能进行移动，即第一次进入该循环时
        if pst_match_status['time'] > 0:
            step_info = StepInfo.from_dict(pst_match_status, map_info)
        else:
            step_info = None

        # 调用路径规划算法
        fly_plane, purchase_uav = algorithm_calculation_fun(map_info, step_info, mp_pool)

        fly_plane_send['UAV_info'] = fly_plane
        fly_plane_send['purchase_UAV'] = purchase_uav

        time_span = time.time() - step_time_start
        time_span_list.append(time_span)
        print('Match time %s, plan time %s s' % (pst_match_status["time"], time_span))

        if time_span >= 1:
            time_out_count += 1
            time_out_stats[step_info.time] = time_span
            print('\033[1;31m%s\033[0m' % 'Timeout!' * 20)

        # 发送飞行计划
        n_ret = send_judger_data(h_socket, fly_plane_send)
        if n_ret != 0:
            return n_ret

        # 接受当前比赛状态
        n_ret, pst_match_status = recv_judger_data(h_socket)
        if n_ret != 0:
            return n_ret

        if pst_match_status["match_status"] == 1:
            step_info = StepInfo.from_dict(pst_match_status, map_info)
            we_uav_value, enemy_uav_value = 0, 0
            for uav_w in step_info.uav_we.values():
                if uav_w.status != UAVStatus.CRASHED:
                    we_uav_value += uav_w.price
            for uav_e in step_info.uav_enemy.values():
                if uav_e.status != UAVStatus.CRASHED:
                    enemy_uav_value += uav_e.price
            print("game over, we value %d, enemy value %d" %
                  (step_info.we_value + we_uav_value, step_info.enemy_value + enemy_uav_value))
            print("\033[1;31mTimeout count %d, stats %s\033[0m" % (time_out_count, time_out_stats))
            print("\033[1;31mMean time %f, max time %f\033[0m" %
                  (sum(time_span_list) / len(time_span_list),
                   max(time_span_list)))
            h_socket.close()
            return 0


if __name__ == "__main__":
    # pool = multiprocessing.Pool(8)

    # 100 * 100
    main('59.110.142.4', 31739, 'd531e946-5ba6-47fd-b39b-1304a92491f2')
    #     "59.110.142.4", 31933, "7c2907df-3aa8 - 44f1-ae08-75ea542d1117"

    # 20 * 20
    # main('123.56.15.18', 31916, '848c0643-0de0-4006-a5e0-c2ac1aa88c23')

    # if len(sys.argv) == 4:
    #     print("Server Host: " + sys.argv[1])
    #     print("Server Port: " + sys.argv[2])
    #     print("Auth Token: " + sys.argv[3])
    #     main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
    # else:
    #     print("need 3 arguments")

    # pool.close()
    # pool.join()
