import time

from jpsp_c_api import jpsp_bridge as bridge


def _test_vector_loc():
    print("Testing `VectorLoc`...")

    vector_loc = bridge.VectorLoc()

    loc = bridge.XYLoc(0, 0)

    print(loc.x)

    start = time.time()
    for i in range(100):
        vector_loc.push(bridge.XYLoc(0, i).cref)
    end = time.time()

    print("Pushed %d XYLoc" % len(vector_loc))

    index = 2
    print('The %dth obj is %s' % (index, str(vector_loc[index])))

    vector_loc.clear()
    print("Cleared, length is %d" % len(vector_loc))

    print(vector_loc)

    print('Time %s\n' % (end - start))


def _test_vector_bool():
    print("Testing `VectorBool`...")

    vector_bool = bridge.VectorBool()

    start = time.time()
    for i in range(100):
        vector_bool.push(False)
    end = time.time()

    print("Pushed %d bool" % len(vector_bool))

    index = 2
    print('The %dth obj is %s' % (index, str(vector_bool[index])))

    vector_bool.clear()
    print("Cleared, lengpathth is %d" % len(vector_bool))

    print(vector_bool)

    print('Time %s\n' % (end - start))


def _test_jpsp_performance():
    print("Testing `JPSPlus` performance...")

    map_size = 20
    # buildings = [(2, 0, 2, 98, 0, 1), (4, 1, 4, 99, 1, 1), (6, 0, 6, 98, 0, 1)]

    buildings = [(2, 3, 2, 16, 0, 8), (3, 9, 4, 9, 0, 9), (5, 3, 5, 16, 0, 5), (9, 3, 9, 16, 0, 6),
                 (13, 3, 13, 16, 0, 6), (14, 6, 14, 7, 0, 8), (15, 5, 15, 5, 0, 8), (16, 4, 16, 4, 0, 7),
                 (17, 3, 17, 3, 0, 7), (15, 8, 15, 9, 0, 9), (16, 10, 16, 11, 0, 9), (17, 12, 17, 13, 0, 6),
                 (18, 14, 18, 15, 0, 7), (19, 16, 19, 17, 0, 8)]

    start = bridge.XYLoc(0, 16)
    end = bridge.XYLoc(13, 7)

    finder = bridge.JPSPlus(map_size, map_size, buildings, search_height=7)
    finder.preprocess()
    finder.print_map(start=start, end=end)

    time_start = time.time()

    # 测试运行时间
    for _ in range(1000):
        path = finder.get_path(start, end)

    # Convert to Coordinate path.
    # path = bridge.to_coord_path(path, 0)

    time_end = time.time()

    print(path)
    if len(path) > 0:
        print("Path found:", end='')
        for i, loc in enumerate(path):
            if i % 10 == 0:
                print()
            if i != len(path) - 1:
                print("(%d, %d)->" % (loc.x, loc.y), end='')
            else:
                print("(%d, %d)" % (loc.x, loc.y))
    else:
        print("Path not found.")

    print("Time span: %s s\n" % (time_end - time_start))


def _test_jpsp_validation():
    def _is_obstacle(loc: bridge.XYLoc, obstacles: list):
        for obstacle in obstacles:
            x1, y1, x2, y2, z1, z2 = obstacle
            if x1 <= loc.x <= x2 and y1 <= loc.y <= y2:
                return True
        return False

    print("Testing `JPSPlus` validation...")

    map_size = 20
    buildings = [(2, 0, 2, 18, 0, 1), (4, 1, 4, 19, 0, 1), (6, 0, 6, 18, 0, 1),
                 (8, 0, 8, 10, 0, 1), (9, 11, 9, 19, 0, 1), (10, 0, 10, 10, 0, 1)]

    finder = bridge.JPSPlus(map_size, map_size, buildings, search_height=7)
    finder.preprocess()
    finder.print_map()

    time_start = time.time()

    flag, count = True, 0
    # 测试可达性
    for start_x in range(map_size):
        for start_y in range(map_size):
            for end_x in range(map_size):
                for end_y in range(map_size):
                    start_point = bridge.XYLoc(start_x, start_y)
                    end_point = bridge.XYLoc(end_x, end_y)
                    if not _is_obstacle(start_point, buildings) and \
                            not _is_obstacle(end_point, buildings) and start_point != end_point:
                        path = finder.get_path(start_point, end_point)
                        flag = flag and True if path else False
                        if not path:
                            break
                        count += 1

    time_end = time.time()

    if flag:
        print("Path found, rounds %d, time %s" % (count, time_end - time_start))
        # for point in path:
        #     print(point)
    else:
        print("Path not found, time %s" % (time_end - time_start))


if __name__ == '__main__':
    _test_vector_loc()
    _test_vector_bool()
    _test_jpsp_performance()
    _test_jpsp_validation()
