import os
import platform
from ctypes import *

from model import Coordinate

this_path = os.path.dirname(os.path.abspath(__file__))
# class level loading lib
if platform.system() == 'Windows':
    libjpsp = cdll.LoadLibrary(os.path.join(this_path, 'libjpsp.dll'))
elif platform.system() == 'Linux':
    libjpsp = cdll.LoadLibrary(os.path.join(this_path, 'libjpsp.so'))
else:
    raise EnvironmentError('Not supported platform.')


class XYLoc:
    libjpsp.new_xy_loc.restype = c_void_p
    libjpsp.new_xy_loc.argtypes = [c_int16, c_int16]
    libjpsp.get_x.restype = c_int16
    libjpsp.get_x.argtypes = [c_void_p]
    libjpsp.get_y.restype = c_int16
    libjpsp.get_y.argtypes = [c_void_p]

    def __init__(self, x, y):
        self._xy_loc = libjpsp.new_xy_loc(x, y)

    def __repr__(self):
        return "(%d, %d)" % (self.x, self.y)

    def __str__(self):
        return "(%d, %d)" % (self.x, self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    @staticmethod
    def from_obj(obj):
        x = libjpsp.get_x(obj)
        y = libjpsp.get_y(obj)
        return XYLoc(x, y)

    @property
    def cref(self):
        return self._xy_loc

    def set_cref(self, ref):
        self._xy_loc = ref

    @property
    def x(self):
        return libjpsp.get_x(self._xy_loc)

    @property
    def y(self):
        return libjpsp.get_y(self._xy_loc)


class VectorLoc(object):
    libjpsp.new_vector_loc.restype = c_void_p
    libjpsp.new_vector_loc.argtypes = []
    libjpsp.new_vector_loc_arg.restype = c_void_p
    libjpsp.new_vector_loc_arg.argtypes = [c_int, c_bool]
    libjpsp.delete_vector_loc.restype = None
    libjpsp.delete_vector_loc.argtypes = [c_void_p]
    libjpsp.clear_vector_loc.restype = None
    libjpsp.clear_vector_loc.argtypes = [c_void_p]
    libjpsp.vector_loc_size.restype = c_int
    libjpsp.vector_loc_size.argtypes = [c_void_p]
    libjpsp.vector_loc_get.restype = c_void_p
    libjpsp.vector_loc_get.argtypes = [c_void_p, c_int]
    libjpsp.vector_loc_set.restype = None
    libjpsp.vector_loc_set.argtypes = [c_void_p, c_int, c_void_p]
    libjpsp.vector_loc_push_back.restype = None
    libjpsp.vector_loc_push_back.argtypes = [c_void_p, c_void_p]

    def __init__(self, ref=None, size=None, value=None):
        if ref:
            self._vector_loc = ref
        elif size:
            self._vector_loc = libjpsp.new_vector_loc_arg(size, value)
        else:
            self._vector_loc = libjpsp.new_vector_loc()  # pointer to new vector

    def __del__(self):
        # when reference count hits 0 in Python,
        libjpsp.delete_vector_loc(self._vector_loc)  # call C++ vector destructor

    def __len__(self):
        return libjpsp.vector_loc_size(self._vector_loc)

    def __getitem__(self, i):
        # access elements in vector at index
        if 0 <= i < len(self):
            return XYLoc.from_obj(
                libjpsp.vector_loc_get(self._vector_loc, c_int(i)))
        raise IndexError('VectorLoc index out of range')

    def __setitem__(self, key, value):
        if 0 <= key < len(self):
            libjpsp.vector_loc_set(self._vector_loc, c_int(key), value)
        else:
            IndexError('VectorLoc index out of range')

    def __repr__(self):
        return '[%s]' % ', '.join(
            [str(self[i]) for i in range(len(self))])

    @property
    def cref(self):
        return self._vector_loc

    def set_cref(self, ref):
        self._vector_loc = ref

    def push(self, loc):
        # push calls vector's push_back
        libjpsp.vector_loc_push_back(self._vector_loc, loc)

    def clear(self):
        libjpsp.clear_vector_loc(self._vector_loc)


class VectorBool(object):
    libjpsp.new_vector_bool.restype = c_void_p
    libjpsp.new_vector_bool.argtypes = []
    libjpsp.new_vector_bool_arg.restype = c_void_p
    libjpsp.new_vector_bool_arg.argtypes = [c_int, c_bool]
    libjpsp.delete_vector_bool.restype = None
    libjpsp.delete_vector_bool.argtypes = [c_void_p]
    libjpsp.clear_vector_bool.restype = None
    libjpsp.clear_vector_bool.argtypes = [c_void_p]
    libjpsp.vector_bool_size.restype = c_int
    libjpsp.vector_bool_size.argtypes = [c_void_p]
    libjpsp.vector_bool_get.restype = c_bool
    libjpsp.vector_bool_get.argtypes = [c_void_p, c_int]
    libjpsp.vector_bool_set.restype = None
    libjpsp.vector_bool_set.argtypes = [c_void_p, c_int, c_bool]
    libjpsp.vector_bool_push_back.restype = None
    libjpsp.vector_bool_push_back.argtypes = [c_void_p, c_bool]

    def __init__(self, ref=None, size=None, value=False):
        if ref:
            self._vector_bool = ref
        elif size:
            self._vector_bool = libjpsp.new_vector_bool_arg(size, value)
        else:
            self._vector_bool = libjpsp.new_vector_bool()  # pointer to new vector

    def __del__(self):
        # when reference count hits 0 in Python,
        libjpsp.delete_vector_bool(self._vector_bool)  # call C++ vector destructor

    def __len__(self):
        return libjpsp.vector_bool_size(self._vector_bool)

    def __getitem__(self, i):
        # access elements in vector at index
        if 0 <= i < len(self):
            return libjpsp.vector_bool_get(self._vector_bool, c_int(i))
        raise IndexError('VectorBool index out of range')

    def __setitem__(self, key, value):
        if 0 <= key < len(self):
            libjpsp.vector_bool_set(self._vector_bool, c_int(key), value)
        else:
            IndexError('VectorBool index out of range')

    def __repr__(self):
        return '[%s]' % ', '.join(
            [str(self[i]) for i in range(len(self))])

    @property
    def cref(self):
        return self._vector_bool

    def set_cref(self, ref):
        self._vector_bool = ref

    def push(self, loc):
        # push calls vector's push_back
        libjpsp.vector_bool_push_back(self._vector_bool, loc)

    def clear(self):
        libjpsp.clear_vector_bool(self._vector_bool)


class JPSPlus:
    libjpsp.new_jpsp_wrapper.restype = c_void_p
    libjpsp.new_jpsp_wrapper.argtypes = [c_void_p, c_int, c_int]
    libjpsp.preprocess.restype = None
    libjpsp.preprocess.argtypes = [c_void_p]
    libjpsp.get_path.restype = c_void_p
    libjpsp.get_path.argtypes = [c_void_p, c_void_p, c_void_p]

    def __init__(self, width, height, buildings: [tuple], search_height: int):
        self._width = width
        self._height = height
        self._map = VectorBool(size=width * height, value=True)

        # Init map data.
        for building in buildings:
            x1, y1, x2, y2, z1, z2 = building
            if z1 <= search_height <= z2:
                for x in range(x1, x2 + 1):
                    for y in range(y1, y2 + 1):
                        self._map[x + y * width] = False

        # Init JPSPlusWrapper obj.
        self._jpsp = libjpsp.new_jpsp_wrapper(
            self._map.cref, width, height)

    def print_map(self, start: XYLoc = None, end: XYLoc = None):
        padding = self._width + 8
        print("\n%s Map %s" % ("#" * padding, "#" * padding))

        # Print x coordinate.
        for i in range(self._width + 1):
            if i == 0:
                print("   ", end="")
            else:
                print("\033[1;31m%d%s\033[0m" % ((i - 1), " " * (3 - len(str(i)))), end='')
        print()

        # Print rows.
        for i in range(self._height):
            print("\033[1;31m%d%s\033[0m" % (i, " " * (3 - len(str(i)))), end='')

            for j in range(self._width):
                if (start and i == start.y and j == start.x) or \
                        (end and i == end.y and j == end.x):
                    print("\033[1;31m%s%s\033[0m" % (int(self._map[j + i * self._width]), " " * 2), end='')
                else:
                    print('%s%s' % (int(self._map[j + i * self._width]), " " * 2), end='')
            print()

        print("%s Map %s\n" % ("#" * padding, "#" * padding))

    def preprocess(self):
        # Preprocess map info.
        libjpsp.preprocess(self._jpsp)

    def get_path(self, start: XYLoc, end: XYLoc):
        path = libjpsp.get_path(self._jpsp, start.cref, end.cref)
        return VectorLoc(ref=path)
        # return path


def xy_loc_to_coord(loc: XYLoc, height: int):
    return Coordinate(loc.x, loc.y, height)


def to_coord_path(path: VectorLoc, height: int):
    return [xy_loc_to_coord(path[i], height) for i in range(len(path))]
