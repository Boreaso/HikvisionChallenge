import time

from jpsp_boost import libjpsp


class JPSPMap:
    def __init__(self, width, height, buildings: [tuple] = None):
        self.width = width
        self.height = height
        self.map_data = libjpsp.VecBool()

        for _ in range(width * height):
            self.map_data.append(True)

        for building in buildings:
            x1, y1, x2, y2, z1, z2 = building
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    self.map_data[x + y * width] = False

    @property
    def get_map(self):
        return self.map_data

    @staticmethod
    def get_test_map():
        test_map = [[1] * 5 for _ in range(5)]
        for i in range(1, 5):
            test_map[2][i] = 0
        test_map[3][0] = 0

        vec_bool = libjpsp.VecBool()
        for i in range(5):
            row = []
            for j in range(5):
                row.append(test_map[i][j])
                vec_bool.append(bool(test_map[i][j] == 1))
            # print(row)

        return vec_bool


map_size = 100
buildings = [(2, 0, 2, 98, 0, 1), (4, 1, 4, 99, 1, 1), (6, 0, 6, 98, 0, 1)]

start = libjpsp.XYLoc(0, 0)
end = libjpsp.XYLoc(99, 0)

jpsp_map = JPSPMap(map_size, map_size, buildings)

finder = libjpsp.JPSPWrapper(jpsp_map.map_data, map_size, map_size)
finder.preprocess()

time_start = time.time()

for _ in range(1000):
    path = finder.get_path(start, end)

time_end = time.time()

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

print("Time span: %s s" % (time_end - time_start))
