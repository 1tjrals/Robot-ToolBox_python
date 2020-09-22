#!/usr/bin/env python

import numpy as np
from roboticstoolbox.robot.ETS import ETS
from roboticstoolbox.robot.ERobot import ERobot
from roboticstoolbox.robot.ELink import ELink


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

        deg = np.pi/180
        mm = 1e-3
        tool_offset = (103)*mm

        l0 = ELink(
            ETS.tz(0.333) * ETS.rz(),
            name='link0',
            parent=None
        )

        l1 = ELink(
            ETS.rx(-90*deg) * ETS.rz(),
            name='link1',
            parent=l0
        )

        l2 = ELink(
            ETS.rx(90*deg) * ETS.tz(0.316) * ETS.rz(),
            name='link2',
            parent=l1
        )

        l3 = ELink(
            ETS.tx(0.0825) * ETS.rx(90*deg) * ETS.rz(),
            name='link3',
            parent=l2
        )

        l4 = ELink(
            ETS.tx(-0.0825) * ETS.rx(-90*deg) * ETS.tz(0.384) * ETS.rz(),
            name='link4',
            parent=l3
        )

        l5 = ELink(
            ETS.rx(90*deg) * ETS.rz(),
            name='link5',
            parent=l4
        )

        l6 = ELink(
            ETS.tx(0.088) * ETS.rx(90*deg) * ETS.tz(0.107) * ETS.rz(),
            name='link6',
            parent=l5
        )

        ee = ELink(
            ETS.tz(tool_offset) * ETS.rz(-np.pi/4),
            name='ee',
            parent=l6
        )

        elinks = [l0, l1, l2, l3, l4, l5, l6, ee]

        super(Panda, self).__init__(
            elinks,
            name='Panda',
            manufacturer='Franka Emika')

        self._qz = np.array([0, 0, 0, 0, 0, 0, 0])
        self._qr = np.array([0, -0.3, 0, -2.2, 0, 2.0, np.pi/4])

    @property
    def qz(self):
        return self._qz

    @property
    def qr(self):
        return self._qr
