#!/usr/bin/env python

import numpy as np
from roboticstoolbox.robot.ERobot import ERobot


class YuMi(ERobot):
    """
    Class that imports an ABB YuMi URDF model

    ``YuMi()`` is a class which imports an ABB YuMi (IRB14000) robot definition
    from a URDF file.  The model describes its kinematic and graphical
    characteristics.

    .. runblock:: pycon

        >>> import roboticstoolbox as rtb
        >>> robot = rtb.models.URDF.YuMi()
        >>> print(robot)

    Defined joint configurations are:

    - qz, zero joint angle configuration, 'L' shaped configuration
    - qr, vertical 'READY' configuration

    :reference:
        - `https://github.com/OrebroUniversity/yumi <https://github.com/OrebroUniversity/yumi>`_

    .. codeauthor:: Jesse Haviland
    .. sectionauthor:: Peter Corke
    """
    def __init__(self):

        args = super().urdf_to_ets_args(
            "yumi_description/urdf/yumi.urdf.xacro")

        super().__init__(
                args[0],
                name=args[1],
                manufacturer='Interbotix'
            )

        self.addconfiguration(
            "qz", np.array([0, 0, 0, 0, 0, 0, 0]))
        self.addconfiguration(
            "qr", np.array([0, -0.3, 0, -2.2, 0, 2.0, np.pi/4]))


if __name__ == '__main__':   # pragma nocover

    robot = YuMi()
    print(robot)
