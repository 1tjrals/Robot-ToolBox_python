#!/usr/bin/env python

import numpy as np
from numpy.linalg import qr
from roboticstoolbox.robot.ETS import ETS
from roboticstoolbox.robot.ERobot import ERobot
from roboticstoolbox.robot.ELink import ELink

from roboticstoolbox.robot.etsnew import ET
import sympy
import cProfile
import roboticstoolbox as rtb


class Panda(ERobot):
    """
    Create model of Franka-Emika Panda manipulator

    panda = Panda() creates a robot object representing the Franka-Emika
    Panda robot arm. This robot is represented using the elementary
    transform sequence (ETS).

    ETS taken from [1] based on
    https://frankaemika.github.io/docs/control_parameters.html

    :references:
        - Kinematic Derivatives using the Elementary Transform
          Sequence, J. Haviland and P. Corke

    """

    def __init__(self):

        deg = np.pi / 180
        mm = 1e-3
        tool_offset = (103) * mm

        l0 = ELink(ETS.tz(0.333) * ETS.rz(), name="link0", parent=None)

        l1 = ELink(ETS.rx(-90 * deg) * ETS.rz(), name="link1", parent=l0)

        l2 = ELink(ETS.rx(90 * deg) * ETS.tz(0.316) * ETS.rz(), name="link2", parent=l1)

        l3 = ELink(
            ETS.tx(0.0825) * ETS.rx(90, "deg") * ETS.rz(), name="link3", parent=l2
        )

        l4 = ELink(
            ETS.tx(-0.0825) * ETS.rx(-90, "deg") * ETS.tz(0.384) * ETS.rz(),
            name="link4",
            parent=l3,
        )

        l5 = ELink(ETS.rx(90, "deg") * ETS.rz(), name="link5", parent=l4)

        l6 = ELink(
            ETS.tx(0.088) * ETS.rx(90, "deg") * ETS.tz(0.107) * ETS.rz(),
            name="link6",
            parent=l5,
        )

        ee = ELink(ETS.tz(tool_offset) * ETS.rz(-np.pi / 4), name="ee", parent=l6)

        elinks = [l0, l1, l2, l3, l4, l5, l6, ee]

        # super(Panda, self).__init__(
        #     elinks,
        #     name='Panda',
        #     manufacturer='Franka Emika')

        # self.addconfiguration(
        #     "qz", np.array([0, 0, 0, 0, 0, 0, 0]))
        # self.addconfiguration(
        #     "qr", np.array([0, -0.3, 0, -2.2, 0, 2.0, np.pi/4]))


if __name__ == "__main__":  # pragma nocover

    # robot = Panda()
    # print(robot)

    x = sympy.symbols("x")

    e1 = ET.Rx()

    e2 = ET.Ry(0.7)

    # print(e1.T(0.7))
    # print(e2.T())

    # ets = e1 * e2
    q = np.array([1.0])
    base = np.eye(4)
    tool = np.eye(4)

    # print(ets.fkine(q, base, tool))
    # print(ets.fkine(q, None, None))
    # print(e1.T(1.0) @ e2.T())

    ets = (
        ET.tz(0.333)
        * ET.Rz()
        * ET.Rx(-np.pi / 2)
        * ET.Rz()
        * ET.ty(-0.316)
        * ET.Rx(np.pi / 2)
        * ET.Rz()
        * ET.tx(0.0825)
        * ET.Rx(np.pi / 2)
        * ET.Rz()
        * ET.tx(-0.0825)
        * ET.ty(0.384)
        * ET.Rx(-np.pi / 2)
        * ET.Rz()
        * ET.Rx(np.pi / 2)
        * ET.Rz()
        * ET.tx(0.088)
        * ET.Rx(np.pi / 2)
        * ET.Rz()
        * ET.tz(0.107)
    )

    print(ets.fkine(q, base, tool))
    # print(e1.__axis_to_number(e1.axis))

    # print(e1 * e2)

    # print(e1.T_OLD(x))

    num = 1000000
    # q = np.random.rand(num)

    # def step_old():
    #     for i in range(num):
    #         e1.T_OLD(q[i])

    # def step_new():
    #     # ls = []
    #     for i in range(num):
    #         e1.T(q[i])

    #     # res = map(e1.T, q)
    #     # list(res)

    #     # ls = [e1.T(x) for x in q]

    def step():
        for i in range(num):
            ets.fkine(q, base, tool)

    cProfile.run("step()")

    r = rtb.models.Panda()

    q = r.qr

    def step_old():
        for i in range(num):
            r.jacob0(q, fast=True)

    cProfile.run("step_old()")

    # # cProfile.run("step_old()")

    # cProfile.run("step_new()")

    # print(e1.T(x))
