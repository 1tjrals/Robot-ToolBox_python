from collections import UserList
from abc import ABC
import numpy as np
from spatialmath.base import trotx, troty, trotz, issymbol
import fknm
import sympy
import math
from copy import deepcopy

# from spatialmath import base

from spatialmath.base import getvector

from spatialmath import SE3

from typing import Optional, Callable, Union
from numpy.typing import ArrayLike, NDArray

try:  # pragma: no cover
    import sympy

    # Sym = sympy.Expr
    Sym = sympy.core.symbol.Symbol

except ImportError:  # pragma: no cover
    Sym = float


class BaseET:
    def __init__(
        self,
        axis: str,
        eta: Union[float, Sym, None] = None,
        axis_func: Optional[Callable[[Union[float, Sym]], NDArray[np.float64]]] = None,
        T: Optional[NDArray[np.float64]] = None,
        jindex: Optional[int] = None,
        unit: str = "rad",
        flip: bool = False,
        qlim: Optional[ArrayLike] = None,
    ):
        self._axis = axis

        if eta is None:
            self._eta = None
        else:
            if axis[0] == "R" and unit.lower().startswith("deg"):
                if not issymbol(eta):
                    self.eta = np.deg2rad(float(eta))
            else:
                self.eta = eta

        self._axis_func = axis_func
        self._flip = flip
        self._jindex = jindex
        if qlim is not None:
            qlim = np.array(getvector(qlim, 2, out="array"))
        self._qlim = qlim

        if self.eta is None:
            if T is None:
                self._joint = True
                self._T = np.eye(4)
                if axis_func is None:
                    raise TypeError("For a variable joint, axis_func must be specified")
            else:
                self._joint = False
                self._T = T
        else:
            self._joint = False
            if axis_func is not None:
                self._T = axis_func(self.eta)
            else:
                raise TypeError(
                    "For a static joint either both `eta` and `axis_func` "
                    "must be specified otherwise `T` must be supplied"
                )

        # Initialise the C object which holds ET data
        # This returns a reference to said C data
        self.__fknm = self.__init_c()

    def __init_c(self):
        """
        Super Private method which initialises a C object to hold ET Data
        """
        if self.jindex is None:
            jindex = 0
        else:
            jindex = self.jindex

        if self.qlim is None:
            qlim = np.array([0, 0])
        else:
            qlim = self.qlim

        return fknm.ET_init(
            self.isjoint,
            self.isflip,
            jindex,
            self.__axis_to_number(self.axis),
            self._T,
            qlim,
        )

    def __update_c(self):
        """
        Super Private method which updates the C object which holds ET Data
        """
        if self.jindex is None:
            jindex = 0
        else:
            jindex = self.jindex

        if self.qlim is None:
            qlim = np.array([0, 0])
        else:
            qlim = self.qlim

        fknm.ET_update(
            self.fknm,
            self.isjoint,
            self.isflip,
            jindex,
            self.__axis_to_number(self.axis),
            self._T,
            qlim,
        )

    def __mul__(self, other: Union["ET", "ETS"]) -> "ETS":
        return ETS([self, other])

    def __add__(self, other: Union["ET", "ETS"]) -> "ETS":
        return self.__mul__(other)

    def __str__(self):

        eta_str = ""

        if self.isjoint:
            if self.jindex is None:
                eta_str = "q"
            else:
                eta_str = f"q{self.jindex}"
        elif issymbol(self.eta):
            # Check if symbolic
            eta_str = f"{self.eta}"
        else:
            eta_str = f"{self.eta}"

        return f"{self.axis}({eta_str})"

    def __repr__(self):

        s_eta = "" if self.eta is None else f"eta={self.eta}"
        s_T = (
            f"T={repr(self._T)}"
            if (self.eta is None and self.axis_func is None)
            else ""
        )
        s_flip = "" if not self.isflip else f"flip={self.isflip}"
        s_qlim = "" if self.qlim is None else f"qlim={repr(self.qlim)}"
        s_jindex = "" if self.jindex is None else f"jindex={self.jindex}"

        kwargs = [s_eta, s_T, s_jindex, s_flip, s_qlim]
        s_kwargs = ", ".join(filter(None, kwargs))

        return f"ET.{self.axis}({s_kwargs})"

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        for k, v in self.__dict__.items():
            if k != "_BaseET__fknm":
                setattr(result, k, deepcopy(v, memo))

        result.__fknm = result.__init_c()
        return result

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __axis_to_number(self, axis: str) -> int:
        """
        Private convenience function which converts the axis string to an
        integer for faster processing in the C extensions
        """
        if axis[0] == "R":
            if axis[1] == "x":
                return 0
            elif axis[1] == "y":
                return 1
            elif axis[1] == "z":
                return 2
        elif axis[0] == "t":
            if axis[1] == "x":
                return 3
            elif axis[1] == "y":
                return 4
            elif axis[1] == "z":
                return 5
        return 0

    @property
    def fknm(self):
        return self.__fknm

    @property
    def eta(self) -> Union[float, Sym, None]:
        """
        Get the transform constant

        :return: The constant η if set
        :rtype: float, symbolic or None

        Example:

        .. runblock:: pycon

            >>> from roboticstoolbox import ET
            >>> e = ET.tx(1)
            >>> e.eta
            >>> e = ET.Rx(90, 'deg')
            >>> e.eta
            >>> e = ET.ty()
            >>> e.eta

        .. note:: If the value was given in degrees it will be converted and
            stored internally in radians
        """
        return self._eta

    @eta.setter
    def eta(self, value: Union[float, Sym]) -> None:
        """
        Set the transform constant

        :param value: The transform constant η
        :type value: float, symbolic or None

        .. note:: No unit conversions are applied, it is assumed to be in
            radians.
        """
        self._eta = value if issymbol(value) else float(value)

    @property
    def axis_func(
        self,
    ) -> Union[Callable[[Union[float, Sym]], NDArray[np.float64]], None]:
        return self._axis_func

    @property
    def axis(self) -> str:
        """
        The transform type and axis

        :return: The transform type and axis
        :rtype: str

        Example:

        .. runblock:: pycon

            >>> from roboticstoolbox import ET
            >>> e = ET.tx(1)
            >>> e.axis
            >>> e = ET.Rx(90, 'deg')
            >>> e.axis

        """
        return self._axis

    @property
    def isjoint(self) -> bool:
        """
        Test if ET is a joint

        :return: True if a joint
        :rtype: bool

        Example:

        .. runblock:: pycon

            >>> from roboticstoolbox import ET
            >>> e = ET.tx(1)
            >>> e.isjoint
            >>> e = ET.tx()
            >>> e.isjoint
        """
        return self._joint

    @property
    def isflip(self) -> bool:
        """
        Test if ET joint is flipped

        :return: True if joint is flipped
        :rtype: bool

        A flipped joint uses the negative of the joint variable, ie. it rotates
        or moves in the opposite direction.

        Example:

        .. runblock:: pycon

            >>> from roboticstoolbox import ET
            >>> e = ET.tx()
            >>> e.T(1)
            >>> eflip = ET.tx(flip=True)
            >>> eflip.T(1)
        """
        return self._flip

    @property
    def isrotation(self) -> bool:
        """
        Test if ET is a rotation

        :return: True if a rotation
        :rtype: bool

        Example:

        .. runblock:: pycon

            >>> from roboticstoolbox import ET
            >>> e = ET.tx(1)
            >>> e.isrotation
            >>> e = ET.rx()
            >>> e.isrotation
        """
        return self.axis[0] == "R"

    @property
    def istranslation(self) -> bool:
        """
        Test if ET is a translation

        :return: True if a translation
        :rtype: bool

        Example:

        .. runblock:: pycon

            >>> from roboticstoolbox import ET
            >>> e = ET.tx(1)
            >>> e.istranslation
            >>> e = ET.rx()
            >>> e.istranslation
        """
        return self.axis[0] == "t"

    @property
    def qlim(self) -> Union[NDArray[np.float64], None]:
        return self._qlim

    @property
    def jindex(self) -> Union[int, None]:
        """
        Get ET joint index

        :return: The assigmed joint index
        :rtype: int or None

        Allows an ET to be associated with a numbered joint in a robot.

        Example:

        .. runblock:: pycon

            >>> from roboticstoolbox import ET
            >>> e = ET.tx()
            >>> print(e)
            >>> e = ET.tx(j=3)
            >>> print(e)
            >>> print(e.jindex)
        """
        return self._jindex

    @jindex.setter
    def jindex(self, j):
        if not isinstance(j, int) or j < 0:
            raise TypeError(f"jindex is {j}, must be an int >= 0")
        self._jindex = j
        self.__update_c()

    @property
    def iselementary(self) -> bool:
        """
        Test if ET is an elementary transform

        :return: True if an elementary transform
        :rtype: bool

        .. note:: ET's may not actually be "elementary", it can be a complex
            mix of rotations and translations.

        :seealso: :func:`compile`
        """
        return self.axis[0] != "S"

    def inv(self):
        r"""
        Inverse of ET

        :return: [description]
        :rtype: ET instance

        The inverse of a given ET.

        Example:

        .. runblock:: pycon

            >>> from roboticstoolbox import ET
            >>> e = ET.Rz(2.5)
            >>> print(e)
            >>> print(e.inv())

        """  # noqa

        inv = deepcopy(self)

        if inv.isjoint:
            inv._flip ^= True
        elif not inv.iselementary:
            inv._T = np.linalg.inv(inv._T)
        elif inv._eta is not None:
            inv._T = np.linalg.inv(inv._T)
            inv._eta = -inv._eta

        inv.__update_c()

        return inv

    def T(self, q: Union[float, Sym] = 0.0) -> NDArray[np.float64]:
        """
        Evaluate an elementary transformation

        :param q: Is used if this ET is variable (a joint)
        :type q: float (radians), required for variable ET's
        :return: The SE(3) or SE(2) matrix value of the ET
        :rtype:  ndarray(4,4) or ndarray(3,3)

        Example:

        .. runblock:: pycon

            >>> from roboticstoolbox import ET
            >>> e = ET.tx(1)
            >>> e.T()
            >>> e = ET.tx()
            >>> e.T(0.7)

        """
        try:
            # Try and use the C implementation, flip is handled in C
            return fknm.ET_T(self.__fknm, q)
        except TypeError:
            # We can't use the fast version, lets use Python instead
            if self.isjoint:
                if self.isflip:
                    q = -1.0 * q

                if self.axis_func is not None:
                    return self.axis_func(q)
                else:  # pragma: no cover
                    raise TypeError("axis_func not defined")
            else:  # pragma: no cover
                return self._T


class ET(BaseET):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def Rx(
        cls, eta: Union[float, Sym, None] = None, unit: str = "rad", **kwargs
    ) -> "ET":
        """
        Pure rotation about the x-axis

        :param η: rotation about the x-axis
        :type η: float
        :param unit: angular unit, "rad" [default] or "deg"
        :type unit: str
        :param j: Explicit joint number within the robot
        :type j: int, optional
        :param flip: Joint moves in opposite direction
        :type flip: bool
        :return: An elementary transform
        :rtype: ETS instance

        - ``ETS.rx(η)`` is an elementary rotation about the x-axis by a
          constant angle η
        - ``ETS.rx()`` is an elementary rotation about the x-axis by a variable
          angle, i.e. a revolute robot joint. ``j`` or ``flip`` can be set in
          this case.

        :seealso: :func:`ETS`, :func:`isrotation`
        :SymPy: supported
        """

        # def axis_func(theta):
        #     ct = base.sym.cos(theta)
        #     st = base.sym.sin(theta)

        #     return np.array(
        #         [[1, 0, 0, 0], [0, ct, -st, 0], [0, st, ct, 0], [0, 0, 0, 1]]
        #     )

        return cls(axis="Rx", eta=eta, axis_func=trotx, unit=unit, **kwargs)

    @classmethod
    def Ry(
        cls, eta: Union[float, Sym, None] = None, unit: str = "rad", **kwargs
    ) -> "ET":
        """
        Pure rotation about the y-axis

        :param η: rotation about the y-axis
        :type η: float
        :param unit: angular unit, "rad" [default] or "deg"
        :type unit: str
        :param j: Explicit joint number within the robot
        :type j: int, optional
        :param flip: Joint moves in opposite direction
        :type flip: bool
        :return: An elementary transform
        :rtype: ETS instance

        - ``ETS.ry(η)`` is an elementary rotation about the y-axis by a
          constant angle η
        - ``ETS.ry()`` is an elementary rotation about the y-axis by a variable
          angle, i.e. a revolute robot joint. ``j`` or ``flip`` can be set in
          this case.

        :seealso: :func:`ETS`, :func:`isrotation`
        :SymPy: supported
        """
        return cls(axis="Ry", eta=eta, axis_func=troty, unit=unit, **kwargs)

    @classmethod
    def Rz(
        cls, eta: Union[float, Sym, None] = None, unit: str = "rad", **kwargs
    ) -> "ET":
        """
        Pure rotation about the z-axis

        :param η: rotation about the z-axis
        :type η: float
        :param unit: angular unit, "rad" [default] or "deg"
        :type unit: str
        :param j: Explicit joint number within the robot
        :type j: int, optional
        :param flip: Joint moves in opposite direction
        :type flip: bool
        :return: An elementary transform
        :rtype: ETS instance

        - ``ETS.rz(η)`` is an elementary rotation about the z-axis by a
          constant angle η
        - ``ETS.rz()`` is an elementary rotation about the z-axis by a variable
          angle, i.e. a revolute robot joint. ``j`` or ``flip`` can be set in
          this case.

        :seealso: :func:`ETS`, :func:`isrotation`
        :SymPy: supported
        """
        return cls(axis="Rz", eta=eta, axis_func=trotz, unit=unit, **kwargs)

    @classmethod
    def tx(cls, eta: Union[float, Sym, None] = None, **kwargs) -> "ET":
        """
        Pure translation along the x-axis

        :param η: translation distance along the z-axis
        :type η: float
        :param j: Explicit joint number within the robot
        :type j: int, optional
        :param flip: Joint moves in opposite direction
        :type flip: bool
        :return: An elementary transform
        :rtype: ETS instance

        - ``ETS.tx(η)`` is an elementary translation along the x-axis by a
          distance constant η
        - ``ETS.tx()`` is an elementary translation along the x-axis by a
          variable distance, i.e. a prismatic robot joint. ``j`` or ``flip``
          can be set in this case.

        :seealso: :func:`ETS`, :func:`istranslation`
        :SymPy: supported
        """

        # this method is 3x faster than using lambda x: transl(x, 0, 0)
        def axis_func(eta):
            # fmt: off
            return np.array([
                [1, 0, 0, eta],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
            # fmt: on

        return cls(axis="tx", axis_func=axis_func, eta=eta, **kwargs)

    @classmethod
    def ty(cls, eta: Union[float, Sym, None] = None, **kwargs) -> "ET":
        """
        Pure translation along the y-axis

        :param η: translation distance along the y-axis
        :type η: float
        :param j: Explicit joint number within the robot
        :type j: int, optional
        :param flip: Joint moves in opposite direction
        :type flip: bool
        :return: An elementary transform
        :rtype: ETS instance

        - ``ETS.ty(η)`` is an elementary translation along the y-axis by a
          distance constant η
        - ``ETS.ty()`` is an elementary translation along the y-axis by a
          variable distance, i.e. a prismatic robot joint. ``j`` or ``flip``
          can be set in this case.

        :seealso: :func:`ETS`, :func:`istranslation`
        :SymPy: supported
        """

        def axis_func(eta):
            # fmt: off
            return np.array([
                [1, 0, 0, 0],
                [0, 1, 0, eta],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
            # fmt: on

        return cls(axis="ty", eta=eta, axis_func=axis_func, **kwargs)

    @classmethod
    def tz(cls, eta: Union[float, Sym, None] = None, **kwargs) -> "ET":
        """
        Pure translation along the z-axis

        :param η: translation distance along the z-axis
        :type η: float
        :param j: Explicit joint number within the robot
        :type j: int, optional
        :param flip: Joint moves in opposite direction
        :type flip: bool
        :return: An elementary transform
        :rtype: ETS instance

        - ``ETS.tz(η)`` is an elementary translation along the z-axis by a
          distance constant η
        - ``ETS.tz()`` is an elementary translation along the z-axis by a
          variable distance, i.e. a prismatic robot joint. ``j`` or ``flip``
          can be set in this case.

        :seealso: :func:`ETS`, :func:`istranslation`
        :SymPy: supported
        """

        def axis_func(eta):
            # fmt: off
            return np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, eta],
                [0, 0, 0, 1]
            ])
            # fmt: on

        return cls(axis="tz", axis_func=axis_func, eta=eta, **kwargs)

    @classmethod
    def SE3(cls, T: Union[NDArray[np.float64], SE3], **kwargs) -> "ET":
        """
        A static SE3

        :param T: The SE3 trnasformation matrix
        :type T: float
        :return: An elementary transform
        :rtype: ET instance

        - ``ET.T(η)`` is an elementary translation along the z-axis by a
          distance constant η
        - ``ETS.tz()`` is an elementary translation along the z-axis by a
          variable distance, i.e. a prismatic robot joint. ``j`` or ``flip``
          can be set in this case.

        :seealso: :func:`ETS`, :func:`istranslation`
        :SymPy: supported
        """

        trans = T.A if isinstance(T, SE3) else T

        return cls(axis="SE3", T=trans, **kwargs)


class ETS(UserList):
    # This is essentially just a container for a list of ET instances

    def __init__(self, arg):
        super().__init__()
        if isinstance(arg, list):
            if not all([isinstance(a, ET) for a in arg]):
                raise ValueError("bad arg")
            # Deep copy the ET's before saving them
            self.data = [deepcopy(et) for et in arg]

        self.__fknm = [et.fknm for et in self.data]

        self._m = len(self.data)
        self._n = len([True for et in self.data if et.isjoint])

    def __str__(self):
        return " * ".join([str(e) for e in self.data])

    def __mul__(self, other: Union["ET", "ETS"]) -> "ETS":
        if isinstance(other, ET):
            return ETS([*self.data, other])
        elif isinstance(other, ETS):
            return ETS([*self.data, *other.data])

    def __rmul__(self, other: Union["ET", "ETS"]) -> "ETS":
        return ETS([other, self.data])

    def fkine(self, q, base=None, tool=None):

        try:
            return fknm.ETS_fkine(self._m, self.__fknm, q, base, tool)
        except:
            pass

    def jacob0(self, q, tool=None):
        r"""
        Manipulator geometric Jacobian in the base frame
        :param q: Joint coordinate vector
        :type q: ndarray(n)
        :param tool: a static tool transformation matrix to apply to the
            end of end, defaults to None
        :type tool: SE3, optional
        :return J: Manipulator Jacobian in the base frame
        :rtype: ndarray(6,n)
        - ``robot.jacob0(q)`` is the manipulator Jacobian matrix which maps
          joint  velocity to end-effector spatial velocity expressed in the
          end-effector frame.
        End-effector spatial velocity :math:`\nu = (v_x, v_y, v_z, \omega_x, \omega_y, \omega_z)^T`
        is related to joint velocity by :math:`{}^{E}\!\nu = \mathbf{J}_m(q) \dot{q}`.

        Example:
        .. runblock:: pycon
            >>> import roboticstoolbox as rtb
            >>> puma = rtb.models.ETS.Puma560()
            >>> puma.jacob0([0, 0, 0, 0, 0, 0])
        """  # noqa

        # Use c extension
        try:
            return fknm.ETS_jacob0(self._m, self._n, self.__fknm, q, tool)
        except TypeError:
            pass

        # # Otherwise use Python
        # if tool is None:
        #     tool = SE3()

        # path, n, _ = self.get_path(end, start)

        # q = getvector(q, self.n)

        # if T is None:
        #     T = self.fkine(q, end=end, start=start, include_base=False) * tool

        # T = T.A
        # U = np.eye(4)
        # j = 0
        # J = np.zeros((6, n))
        # zero = np.array([0, 0, 0])

        # for link in path:

        #     if link.isjoint:
        #         U = U @ link.A(q[link.jindex], fast=True)

        #         if link == end:
        #             U = U @ tool.A

        #         Tu = np.linalg.inv(U) @ T
        #         n = U[:3, 0]
        #         o = U[:3, 1]
        #         a = U[:3, 2]
        #         x = Tu[0, 3]
        #         y = Tu[1, 3]
        #         z = Tu[2, 3]

        #         if link.v.axis == "Rz":
        #             J[:3, j] = (o * x) - (n * y)
        #             J[3:, j] = a

        #         elif link.v.axis == "Ry":
        #             J[:3, j] = (n * z) - (a * x)
        #             J[3:, j] = o

        #         elif link.v.axis == "Rx":
        #             J[:3, j] = (a * y) - (o * z)
        #             J[3:, j] = n

        #         elif link.v.axis == "tx":
        #             J[:3, j] = n
        #             J[3:, j] = zero

        #         elif link.v.axis == "ty":
        #             J[:3, j] = o
        #             J[3:, j] = zero

        #         elif link.v.axis == "tz":
        #             J[:3, j] = a
        #             J[3:, j] = zero

        #         j += 1
        #     else:
        #         A = link.A(fast=True)
        #         if A is not None:
        #             U = U @ A
