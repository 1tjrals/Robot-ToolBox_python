#!/usr/bin/env python

import numpy as np
from roboticstoolbox.robot.ET import ET
from roboticstoolbox.robot.ERobot import ERobot
from roboticstoolbox.robot.ELink import ELink


class XYPanda(ERobot):
    """
    Create model of Franka-Emika Panda manipulator on an XY platform

    xypanda = XYPanda() creates a robot object representing the Franka-Emika
    Panda robot arm mounted on an XY platform. This robot is represented using the elementary
    transform sequence (ETS).

    ETS taken from [1] based on
    https://frankaemika.github.io/docs/control_parameters.html

    :references:
        - Kinematic Derivatives using the Elementary Transform
          Sequence, J. Haviland and P. Corke

    """

    def __init__(self, workspace=5):
        """
        Create model of Franka-Emika Panda manipulator on an XY platform.

        :param workspace: workspace limits in the x and y directions, defaults to 5
        :type workspace: float, optional

        The XY part of the robot has a range -``workspace`` to ``workspace``.
        """

        deg = np.pi / 180
        mm = 1e-3
        tool_offset = (103) * mm

        lx = ELink(ET.tx(), name="link-x", parent=None, qlim=[-workspace, workspace])

        ly = ELink(ET.ty(), name="link-y", parent=lx, qlim=[-workspace, workspace])

        l0 = ELink(ET.tz(0.333) * ET.Rz(), name="link0", parent=ly)

        l1 = ELink(ET.Rx(-90 * deg) * ET.Rz(), name="link1", parent=l0)

        l2 = ELink(ET.Rx(90 * deg) * ET.tz(0.316) * ET.Rz(), name="link2", parent=l1)

        l3 = ELink(ET.tx(0.0825) * ET.Rx(90, "deg") * ET.Rz(), name="link3", parent=l2)

        l4 = ELink(
            ET.tx(-0.0825) * ET.Rx(-90, "deg") * ET.tz(0.384) * ET.Rz(),
            name="link4",
            parent=l3,
        )

        l5 = ELink(ET.Rx(90, "deg") * ET.Rz(), name="link5", parent=l4)

        l6 = ELink(
            ET.tx(0.088) * ET.Rx(90, "deg") * ET.tz(0.107) * ET.Rz(),
            name="link6",
            parent=l5,
        )

        ee = ELink(ET.tz(tool_offset) * ET.Rz(-np.pi / 4), name="ee", parent=l6)

        elinks = [lx, ly, l0, l1, l2, l3, l4, l5, l6, ee]

        super().__init__(elinks, name="XYPanda", manufacturer="Franka Emika")

        self.addconfiguration("qz", np.array([0, 0, 0, 0, 0, 0, 0, 0, 0]))
        self.addconfiguration(
            "qr", np.array([0, 0, 0, -0.3, 0, -2.2, 0, 2.0, np.pi / 4])
        )


if __name__ == "__main__":  # pragma nocover

    robot = XYPanda()
    print(robot)
