import time

from jpsp_python.bridge import buildings_to_obstacle_points, xy_to_point, print_map
from jpsp_python.jps import JPS, Point

# obstacles = [xy_to_point(2, i) for i in range(99)]
# jpsp_python = JPS(width=5, height=5, obstacles=obstacles)

# buildings = [(2, 0, 2, 3, 0, 1)]
# obstacles = buildings_to_obstacle_points(buildings, 0)
# jpsp_python = JPS(width=5, height=5, obstacles=obstacles)
#
# jpsp_python.build_primary_points()
# jpsp_python.build_strait_jump_points()
# jpsp_python.build_diagonal_jump_points()
#
# path = jpsp_python.get_path(start=xy_to_point(0, 0), goal=xy_to_point(4, 0))
#
map_size = 20

start = xy_to_point(0, 16)
end = xy_to_point(13, 7)

pre_start = time.time()
for _ in range(1):
    # buildings = [(2, 0, 2, 8, 0, 1), (4, 1, 4, 9, 1, 1), (6, 0, 6, 8, 0, 1)]
    buildings = [(2, 3, 2, 16, 0, 8), (3, 9, 4, 9, 0, 9), (5, 3, 5, 16, 0, 5), (9, 3, 9, 16, 0, 6),
                 (13, 3, 13, 16, 0, 6), (14, 6, 14, 7, 0, 8), (15, 5, 15, 5, 0, 8), (16, 4, 16, 4, 0, 7),
                 (17, 3, 17, 3, 0, 7), (15, 8, 15, 9, 0, 9), (16, 10, 16, 11, 0, 9), (17, 12, 17, 13, 0, 6),
                 (18, 14, 18, 15, 0, 7), (19, 16, 19, 17, 0, 8)]

    obstacles = buildings_to_obstacle_points(buildings, 1)

    jps = JPS(width=map_size, height=map_size, obstacles=obstacles)

    jps.build_primary_points()
    jps.build_strait_jump_points()
    jps.build_diagonal_jump_points()

    print_map(jps.grid_nodes, width=map_size, height=map_size, start=start, end=end)

print("Preprocess finished, time %s" % (time.time() - pre_start))

time_start = time.time()
flag, count = True, 0

# for start_x in range(map_size):
#     for start_y in range(map_size):
#         for end_x in range(map_size):
#             for end_y in range(map_size):
#                 start_point = xy_to_point(start_x, start_y)
#                 end_point = xy_to_point(end_x, end_y)
#                 if start_point not in obstacles and end_point not in obstacles:
#                     path = jps.get_path(start=start_point, goal=end_point)
#                     flag = flag and True if path else False
#                     if not path:
#                         break
#                     count += 1

for _ in range(1):
    path = jps.get_path(start=xy_to_point(0, 16), goal=xy_to_point(13, 7))
    flag = flag and True if path else False
    count += 1

time_end = time.time()

if flag:
    print("Path found, time %s" % (time_end - time_start))
    # for point in path:
    #     print(point)
else:
    print("Path not found, time %s" % (time_end - time_start))
