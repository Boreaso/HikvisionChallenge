import matplotlib.pyplot as plt
import numpy as np


def random_triangle():
    x1, y1 = 0, 40
    x3, y3 = 200, -10
    x2, y2 = 100, 200
    sample_size = 10
    theta = np.arange(0, 1, 0.001)
    x = theta * x1 + (1 - theta) * x2
    y = theta * y1 + (1 - theta) * y2
    plt.plot(x, y, 'g--', linewidth=2)
    x = theta * x1 + (1 - theta) * x3
    y = theta * y1 + (1 - theta) * y3
    plt.plot(x, y, 'g--', linewidth=2)
    x = theta * x2 + (1 - theta) * x3
    y = theta * y2 + (1 - theta) * y3
    plt.plot(x, y, 'g--', linewidth=2)
    rnd1 = np.random.random(size=sample_size)
    rnd2 = np.random.random(size=sample_size)
    rnd2 = np.sqrt(rnd2)
    x = rnd2 * (rnd1 * x1 + (1 - rnd1) * x2) + (1 - rnd2) * x3
    y = rnd2 * (rnd1 * y1 + (1 - rnd1) * y2) + (1 - rnd2) * y3
    plt.plot(x, y, 'ro')
    plt.grid(True)
    # plt.savefig('demo.png')
    plt.show()


def random_rectangle(width, height, num_points):
    xy = np.random.randint(low=0, high=min(width, height), size=(2, num_points))

    plt.plot(xy[0, :], xy[1, :], 'ro')
    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    random_rectangle(20, 20, 10)
