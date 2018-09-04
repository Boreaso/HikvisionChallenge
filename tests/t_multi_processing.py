import multiprocessing
import time


def f(x):
    for _ in range(100000000):
        x += 10
    return x


def func(msg):
    # print(msg)
    # return
    pass


if __name__ == "__main__":

    pool = multiprocessing.Pool(processes=8)
    start = time.time()

    results = []
    for i in range(64):
        # msg = "hello %d" % i
        result = pool.apply_async(func, (None,))
        results.append(result)

    # print("Mark~ Mark~ Mark~~~~~~~~~~~~~~~~~~~~~~")
    for result in results:
        print(result.get())

    # pool.close()
    # pool.join()  # behind close() or terminate()

    results = []
    for i in range(64):
        # msg = "hello %d" % i
        result = pool.apply_async(func, (None,))
        results.append(result)

    # print("Mark~ Mark~ Mark~~~~~~~~~~~~~~~~~~~~~~")
    for result in results:
        print(result.get())

    # pool.close()
    # pool.join()  # behind close() or terminate()

    end = time.time()

    print("Sub-process(es) done. time %s" % (end - start))

# if __name__ == '__main__':
#     cores = multiprocessing.cpu_count()
#     pool = multiprocessing.Pool(processes=cores)
#     xs = range(5)
#
#     # method 1: map
#     print(pool.map(f, xs))  # prints [0, 1, 4, 9, 16]
#
#     # method 2: imap
#     for y in pool.imap(f, xs):
#         print(y)  # 0, 1, 4, 9, 16, respectively
#
#     cnt = 0
#     for _ in pool.imap_unordered(f, xs):
#         print('done %d/%d\r' % (cnt, len(xs)))
#         cnt += 1
