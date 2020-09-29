#!/usr/bin/env python3
"""
@author: Jesse Haviland
@author: Peter Corke
"""
from collections import UserList, namedtuple
import numpy as np
from spatialmath import SE3


class ETS(UserList):
    """
    This class implements a single elementary transform (ET)

    :param axis_func: The function which calculates the transform of the ET.
    :type axis_func: static et.T__ function
    :param eta: The coordinate of the ET. If not supplied the ET corresponds
        to a variable ET which is a joint
    :type eta: float, optional
    :param joint: If this ET corresponds to a joint, this corresponds to the
        joint number within the robot
    :type joint: int, optional

    :references:
        - Kinematic Derivatives using the Elementary Transform Sequence,
          J. Haviland and P. Corke

    """

    # TODO should probably prefix with __
    STATIC = 0
    VARIABLE = 1
    ets = namedtuple('ETS', 'eta axis_func axis jtype T')

    def __init__(self, axis_func=None, axis=None, eta=None):

        super().__init__()  # init UserList superclass

        if axis_func is None and axis is None and eta is None:
            # ET()
            # create instance with no values
            self.data = []
            return

        if eta is not None:
            # constant value specified
            jtype = self.STATIC
            T = axis_func(eta)
        else:
            # it's a variable joint
            jtype = self.VARIABLE
            T = None

        # Save all the params in a named tuple
        e = self.ets(eta, axis_func, axis, jtype, T)

        # And make it the only value of this instance
        self.data = [e]

    @property
    def eta(self):
        return self.data[0].eta

    @property
    def axis_func(self):
        return self.data[0].axis_func

    @property
    def axis(self):
        return self.data[0].axis

    @property
    def jtype(self):
        return self.data[0].jtype

    def T(self, q=None):
        """
        Calculates the transformation matrix of the ET

        :param q: Is used if this ET is variable (a joint)
        :type q: float (radians), required for variable ET's
        :return: The transformation matrix of the ET
        :rtype: SE3

        """
        if self.jtype is self.STATIC:
            return self.data[0].T
        else:
            return self.axis_func(q)

    def __str__(self):
        """
        Pretty prints the ET. Will output angles in degrees

        :return: The transformation matrix of the ET
        :rtype: str

        """
        es = []
        joint = 0

        # For et in the object, display it, data comes from properties
        # which come from the named tuple
        for et in self:

            if et.jtype is self.STATIC:
                if et.axis[0] == 'R':
                    s = '%s(%g)' % (et.axis, et.eta * 180 / np.pi)
                else:
                    s = '%s(%g)' % (et.axis, et.eta)
            else:
                s = '%s(q%d)' % (et.axis, joint)
                joint += 1
            es.append(s)

        return " * ".join(es)

    # redefine * operator to concatenate the internal lists
    def __mul__(self, rest):
        prod = ETS()
        prod.data = self.data + rest.data
        return prod

    def __rmul__(self, rest):
        prod = ETS()
        prod.data = self.data + rest
        return prod

    # redefine so that indexing returns an ET type
    def __getitem__(self, i):
        item = ETS()
        data = self.data[i]  # can be [2] or slice, eg. [3:5]
        # ensure that data is always a list
        if isinstance(data, list):
            item.data = data
        else:
            item.data = [data]
        return item

    def __repr__(self):
        return str(self)

    @classmethod
    def rx(cls, eta=None):
        """
        An elementary transform (ET). A pure rotation of eta about the x-axis.

        L = TRx(eta) will instantiate an ET object which represents a pure
        rotation about the x-axis by amount eta.

        L = TRx() as above except this ET representation a variable
        rotation, i.e. a joint

        :param eta: The amount of rotation about the x-axis
        :type eta: float (radians)
        :param joint: The joint number within the robot
        :type joint: int
        :return: An ET object
        :rtype: ET

        """
        def axis_func(eta):
            return np.array([
                [1, 0, 0, 0],
                [0, np.cos(eta), -np.sin(eta), 0],
                [0, np.sin(eta), np.cos(eta), 0],
                [0, 0, 0, 1]
            ])

        return cls(axis_func, axis='Rx', eta=eta)

    @classmethod
    def ry(cls, eta=None):
        """
        An elementary transform (ET). A pure rotation of eta about the y-axis.

        L = TRy(eta) will instantiate an ET object which represents a pure
        rotation about the y-axis by amount eta.

        L = TRy() as above except this ET representation a variable
        rotation, i.e. a joint

        :param eta: The amount of rotation about the y-axis
        :type eta: float (radians)
        :param joint: The joint number within the robot
        :type joint: int
        :return: An ET object
        :rtype: ET

        """
        def axis_func(eta):
            return np.array([
                [np.cos(eta), 0, np.sin(eta), 0],
                [0, 1, 0, 0],
                [-np.sin(eta), 0, np.cos(eta), 0],
                [0, 0, 0, 1]
            ])

        return cls(axis_func, axis='Ry', eta=eta)

    @classmethod
    def rz(cls, eta=None):
        """
        An elementary transform (ET). A pure rotation of eta about the z-axis.

        L = TRz(eta) will instantiate an ET object which represents a pure
        rotation about the z-axis by amount eta.

        L = TRz() as above except this ET representation a variable
        rotation, i.e. a joint

        :param eta: The amount of rotation about the z-axis
        :type eta: float (radians)
        :return: An ET object
        :rtype: ET

        """
        def axis_func(eta):
            return np.array([
                [np.cos(eta), -np.sin(eta), 0, 0],
                [np.sin(eta), np.cos(eta), 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])

        return cls(axis_func, axis='Rz', eta=eta)

    @classmethod
    def tx(cls, eta=None):
        """
        An elementary transform (ET). A pure translation of eta along the
        x-axis

        L = Ttx(eta) will instantiate an ET object which represents a pure
        translation along the x-axis by amount eta.

        L = Ttx() as above except this ET representation a variable
        translation, i.e. a joint

        :param eta: The amount of translation along the x-axis
        :type eta: float (metres)
        :return: An ET object
        :rtype: ET

        """
        def axis_func(eta):
            return np.array([
                [1, 0, 0, eta],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])

        return cls(axis_func, axis='tx', eta=eta)

    @classmethod
    def ty(cls, eta=None):
        """
        An elementary transform (ET). A pure translation of eta along the
        x-axis

        L = Tty(eta) will instantiate an ET object which represents a pure
        translation along the y-axis by amount eta.

        L = Tty() as above except this ET representation a variable
        translation, i.e. a joint

        :param eta: The amount of translation along the x-axis
        :type eta: float (metres)
        :return: An ET object
        :rtype: ET

        """
        def axis_func(eta):
            return np.array([
                [1, 0, 0, 0],
                [0, 1, 0, eta],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])

        return cls(axis_func, axis='ty', eta=eta)

        # return cls(SE3.Ty, axis='ty', eta=eta)

    @classmethod
    def tz(cls, eta=None):
        """
        An elementary transform (ET). A pure translation of eta along the
        z-axis

        L = Ttz(eta) will instantiate an ET object which represents a pure
        translation along the z-axis by amount eta.

        L = Ttz() as above except this ET representation a variable
        translation, i.e. a joint

        :param eta: The amount of translation along the x-axis
        :type eta: float (metres)
        :return: An ET object
        :rtype: ET

        """
        def axis_func(eta):
            return np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, eta],
                [0, 0, 0, 1]
            ])

        return cls(axis_func, axis='tz', eta=eta)


# if __name__ == "__main__":

#     from math import pi

#     e = ET.rx(pi/2)
#     print(e)

#     e = ET.rx(pi/2) * ET.tx(0.3) * ET.ty(0.4) * ET.rx(-pi/2)
#     print(e)

#     e = ET.rx(pi/2) * ET.tx() * ET.ty() * ET.rx(-pi/2)
#     print(e)
