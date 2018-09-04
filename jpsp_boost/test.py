import time

from simpleai.search import astar, greedy

from cython_custom import Coordinate
from cython_path_search import RoutePlanningProblem

if __name__ == '__main__':
    time_start = time.time()

    map_info = (199, 199, 10)
    buildings = [(1, 1, 198, 199, 0, 10)]
    start = (0, 0, 0)
    end = (199, 199, 10)

    result = None
    count = 1

    problem = RoutePlanningProblem(
        map_info=map_info,
        buildings=buildings)
    for _ in range(count):
        problem.set_config(start=Coordinate(*start), end=Coordinate(*end))
        result = astar(problem, graph_search=True)

    time_end = time.time()

    path = [(c.x, c.y, c.z) for (_, c) in result.path()]
    print(result.state)
    print(path)
    print('Time: %s s' % ((time_end - time_start) / count))
