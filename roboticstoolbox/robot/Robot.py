import numpy as np
import roboticstoolbox as rtb
from spatialmath import SE3
from spatialmath.base.argcheck import getvector
from roboticstoolbox.robot.Link import Link
from os.path import splitext
from roboticstoolbox.backend import URDF
from roboticstoolbox.backend import xacro

class Robot:

    def __init__(
            self,
            links,
            name='noname',
            manufacturer='',
            base=None,
            tool=None,
            gravity=None,
            urdfdir=None,
            keywords=()):

        self.name = name
        self.manufacturer = manufacturer

        if base is None:
            base = SE3()
        if tool is None:
            tool = SE3()
        self.base = base
        self.tool = tool
        if keywords is not None and not isinstance(keywords, (tuple, list)):
            raise TypeError('keywords must be a list or tuple')
        else:
            self.keywords = keywords
        if gravity is None:
            gravity = np.array([0, 0, 9.81])
        self.gravity = gravity

        if not isinstance(links, list):
            raise TypeError('The links must be stored in a list.')
        for link in links:
            if not isinstance(link, Link):
                raise TypeError('links should all be Link subclass')
            link._robot = self
        self._links = links

        self._configdict = {}

        self._dynchange = True

        # Search mesh dir for meshes
        if urdfdir is not None:
            # Parse the URDF to obtain file paths and scales
            data = self._get_stl_file_paths_and_scales(urdfdir)
            print(data)
            # Obtain the base mesh
            self.basemesh = [data[0][0], data[1][0]]
            # Save the respective meshes to each link
            for idx in range(1, self.n):
                print(idx)
                self._links[idx].mesh = [data[0][idx], data[1][idx]]
        else:
            self.basemesh = None

    def __getitem__(self, i):
        return self._links[i]

    @staticmethod
    def _get_stl_file_paths_and_scales(urdf_path):
        data = [[], []]  # [ [filenames] , [scales] ]

        name, ext = splitext(urdf_path)

        if ext == '.xacro':
            urdf_string = xacro.main(urdf_path)
            urdf = URDF.loadstr(urdf_string, urdf_path)

            for link in urdf.links:
                data[0].append(link.visuals[0].geometry.mesh.filename)
                data[1].append(link.visuals[0].geometry.mesh.scale)

        return data

    def dynchanged(self):
        self._dynchanged = True

    @property
    def n(self):
        return len(self._links)

    def addconfiguration(self, name, q):
        v = getvector(q, self.n)
        self._configdict[name] = v
        setattr(self, name, v)

    # --------------------------------------------------------------------- #
    @property
    def name(self):
        return self._name

    @property
    def manufacturer(self):
        return self._manufacturer

    @property
    def links(self):
        return self._links

    @property
    def base(self):
        return self._base

    @property
    def tool(self):
        return self._tool

    @property
    def gravity(self):
        return self._gravity

    @name.setter
    def name(self, name_new):
        self._name = name_new

    @manufacturer.setter
    def manufacturer(self, manufacturer_new):
        self._manufacturer = manufacturer_new

    @base.setter
    def base(self, T):
        if not isinstance(T, SE3):
            T = SE3(T)
        self._base = T

    @tool.setter
    def tool(self, T):
        if not isinstance(T, SE3):
            T = SE3(T)
        self._tool = T

    @gravity.setter
    def gravity(self, gravity_new):
        self._gravity = getvector(gravity_new, 3, 'col')
        self.dynchanged()

    # --------------------------------------------------------------------- #

    @property
    def q(self):
        return self._q

    @property
    def qd(self):
        return self._qd

    @property
    def qdd(self):
        return self._qdd

    @property
    def control_type(self):
        return self._control_type

    @q.setter
    def q(self, q_new):
        self._q = getvector(q_new, self.n)

    @qd.setter
    def qd(self, qd_new):
        self._qd = getvector(qd_new, self.n)

    @qdd.setter
    def qdd(self, qdd_new):
        self._qdd = getvector(qdd_new, self.n)

    @control_type.setter
    def control_type(self, cn):
        if cn == 'p' or cn == 'v' or cn == 'a':
            self._control_type = cn
        else:
            raise ValueError(
                'Control type must be one of \'p\', \'v\', or \'a\'')
        