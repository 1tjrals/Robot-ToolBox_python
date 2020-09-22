#!/usr/bin/env python

import numpy as np
import roboticstoolbox as rp
from roboticstoolbox.robot.ERobot import ERobot
from pathlib import Path


class vx300s(ERobot):

    def __init__(self):

        mpath = Path(rp.__file__).parent
        fpath = mpath / 'models' / 'xacro' / 'interbotix_descriptions' / 'urdf'
        fname = 'vx300s.urdf.xacro'

        args = super(vx300s, self).urdf_to_ets_args(
            (fpath / fname).as_posix())

        super(vx300s, self).__init__(
            args[0],
            name=args[1])

        self.manufacturer = 'Interbotix'

        self._qz = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0])
        self._qr = np.array([0, -0.3, 0, -2.2, 0, 2.0, np.pi/4, 0, 0])

    @property
    def qz(self):
        return self._qz

    @property
    def qr(self):
        return self._qr
