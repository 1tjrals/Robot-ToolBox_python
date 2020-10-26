import sys
import numpy as np
# import roboticstoolbox as rtb
from spatialmath import SE3
from spatialmath.base.argcheck import isvector, getvector, getmatrix, \
    verifymatrix
from roboticstoolbox.robot.Link import Link
from spatialmath.base.transforms3d import tr2delta, tr2eul
# from roboticstoolbox.backend import URDF
# from roboticstoolbox.backend import xacro
from pathlib import PurePath, PurePosixPath
from scipy.optimize import minimize, Bounds, LinearConstraint


class Robot:

    def __init__(
            self,
            links,
            name='noname',
            manufacturer='',
            base=None,
            tool=None,
            gravity=None,
            meshdir=None,
            keywords=(),
            symbolic=False):

        self.name = name
        self.manufacturer = manufacturer
        self.symbolic = symbolic
        self.base = base
        self.tool = tool
        self.basemesh = None
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

        self._dynchanged = True

        # this probably should go down to DHRobot
        if meshdir is not None:
            classpath = sys.modules[self.__module__].__file__
            self.meshdir = PurePath(classpath).parent / PurePosixPath(meshdir)
            self.basemesh = self.meshdir / "link0.stl"
            for j, link in enumerate(self._links, start=1):
                link.mesh = self.meshdir / "link{:d}.stl".format(j)

        # URDF Parser Attempt
        # # Search mesh dir for meshes
        # if urdfdir is not None:
        #     # Parse the URDF to obtain file paths and scales
        #     data = self._get_stl_file_paths_and_scales(urdfdir)
        #     # Obtain the base mesh
        #     self.basemesh = [data[0][0], data[1][0], data[2][0]]
        #     # Save the respective meshes to each link
        #     for idx in range(1, self.n+1):
        #         self._links[idx-1].mesh = [data[0][idx], data[1][idx],
        #         data[2][idx]]
        # else:
        #     self.basemesh = None

    def __getitem__(self, i):
        """
        Get link

        :param i: link number
        :type i: int
        :return: i'th link of robot
        :rtype: Link subclass

        This also supports iterating over each link in the robot object,
        from the base to the tool.

        .. runblock:: pycon

            >>> import roboticstoolbox as rtb
            >>> robot = rtb.models.DH.Puma560()
            >>> print(robot[1]) # print the 2nd link
            >>> print([link.a for link in robot])  # print all the a_j values

        """
        return self._links[i]

    # URDF Parser Attempt
    # @staticmethod
    # def _get_stl_file_paths_and_scales(urdf_path):
    #     data = [[], [], []]  # [ [filenames] , [scales] , [origins] ]
    #
    #     name, ext = splitext(urdf_path)
    #
    #     if ext == '.xacro':
    #         urdf_string = xacro.main(urdf_path)
    #         urdf = URDF.loadstr(urdf_string, urdf_path)
    #
    #         for link in urdf.links:
    #             data[0].append(link.visuals[0].geometry.mesh.filename)
    #             data[1].append(link.visuals[0].geometry.mesh.scale)
    #             data[2].append(SE3(link.visuals[0].origin))
    #
    #     return data

    def dynchanged(self):
        """
        Dynamic parameters have changed

        Called from a property setter to inform the robot that the cache of
        dynamic parameters is invalid.

        :seealso: :func:`roboticstoolbox.Link._listen_dyn`
        """
        self._dynchanged = True

    def _getq(self, q=None):
        """
        Get joint coordinates

        :param q: passed value, defaults to None
        :type q: array_like, optional
        :return: passed or value from robot state
        :rtype: ndarray(n,)
        """
        if q is None:
            return self.q
        elif isvector(q, self.n):
            return getvector(q, self.n)
        else:
            return getmatrix(q, (None, self.n))

    @property
    def n(self):
        """
        Number of joints

        :return: Number of joints
        :rtype: int

        Example:

        .. runblock:: pycon

            >>> import roboticstoolbox as rtb
            >>> robot = rtb.models.DH.Puma560()
            >>> robot.n

        """
        return len(self._links)

    def addconfiguration(self, name, q):
        """
        Add a named joint configuration

        :param name: Name of the joint configuration
        :type name: str
        :param q: Joint configuration
        :type q: ndarray(n,)

        Example:

        .. runblock:: pycon

            >>> import roboticstoolbox as rtb
            >>> robot = rtb.models.DH.Puma560()
            >>> robot.qz
            >>> robot.addconfiguration("mypos", [0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
            >>> robot.mypos
        """
        v = getvector(q, self.n)
        self._configdict[name] = v
        setattr(self, name, v)

    def dyntable(self):
        """
        Pretty print the dynamic parameters

        Example:

        .. runblock:: pycon

            >>> import roboticstoolbox as rtb
            >>> robot = rtb.models.DH.Puma560()
            >>> robot.dyntable()
        """
        for j, link in enumerate(self):
            print(f"Link {j:d}")
            link.dyntable(indent=4)

# --------------------------------------------------------------------- #
    @property
    def name(self):
        """
        Get/set robot name

        - ``robot.name`` is the robot name

        :return: robot name
        :rtype: str

        - ``robot.name = ...`` checks and sets therobot name
        """
        return self._name

    @name.setter
    def name(self, name_new):
        self._name = name_new

# --------------------------------------------------------------------- #

    @property
    def manufacturer(self):
        """
        Get/set robot manufacturer's name

        - ``robot.manufacturer`` is the robot manufacturer's name

        :return: robot manufacturer's name
        :rtype: str

        - ``robot.manufacturer = ...`` checks and sets the manufacturer's name
        """
        return self._manufacturer

    @manufacturer.setter
    def manufacturer(self, manufacturer_new):
        self._manufacturer = manufacturer_new
# --------------------------------------------------------------------- #

    @property
    def links(self):
        """
        Robot links

        :return: A list of link objects
        :rtype: list of Link subclass instances

        .. note:: It is probably more concise to index the robot object rather
            than the list of links, ie. the following are equivalent::

                robot.links[i]
                robot[i]
        """
        return self._links

# --------------------------------------------------------------------- #

    @property
    def base(self):
        """
        Get/set robot base transform

        - ``robot.base`` is the robot base transform

        :return: robot tool transform
        :rtype: SE3 instance

        - ``robot.base = ...`` checks and sets the robot base transform

        .. note:: The private attribute ``_base`` will be None in the case of
            no base transform, but this property will return ``SE3()`` which
            is an identity matrix.
        """
        if self._base is None:
            return SE3()
        else:
            return self._base

    @base.setter
    def base(self, T):
        # if not isinstance(T, SE3):
        #     T = SE3(T)
        if T is None or isinstance(T, SE3):
            self._base = T
        elif SE3.isvalid(T):
            self._tool = SE3(T, check=False)
        else:
            raise ValueError('base must be set to None (no tool) or an SE3')
# --------------------------------------------------------------------- #

    @property
    def tool(self):
        """
        Get/set robot tool transform

        - ``robot.tool`` is the robot name

        :return: robot tool transform
        :rtype: SE3 instance

        - ``robot.tool = ...`` checks and sets the robot tool transform

        .. note:: The private attribute ``_tool`` will be None in the case of
            no tool transform, but this property will return ``SE3()`` which
            is an identity matrix.
        """
        if self._tool is None:
            return SE3()
        else:
            return self._tool

    @tool.setter
    def tool(self, T):
        # if not isinstance(T, SE3):
        #     T = SE3(T)
        # this is allowed to be none, it's helpful for symbolics rather than
        # having an identity matrix
        if T is None or isinstance(T, SE3):
            self._tool = T
        elif SE3.isvalid(T):
            self._tool = SE3(T, check=False)
        else:
            raise ValueError('tool must be set to None (no tool) or an SE3')

# --------------------------------------------------------------------- #

    @property
    def gravity(self):
        """
        Get/set default gravitational acceleration

        - ``robot.name`` is the default gravitational acceleration

        :return: robot name
        :rtype: ndarray(3,)

        - ``robot.name = ...`` checks and sets default gravitational
          acceleration

        .. note:: If the z-axis is upward, out of the Earth, this should be
            a positive number.
        """
        return self._gravity

    @gravity.setter
    def gravity(self, gravity_new):
        self._gravity = getvector(gravity_new, 3)
        self.dynchanged()

# TODO, the remaining functions, I have only a hazy understanding of how they work
# --------------------------------------------------------------------- #

    @property
    def q(self):
        """
        Get/set robot joint configuration

        - ``robot.q`` is the robot joint configuration

        :return: robot joint configuration
        :rtype: ndarray(n,)

        - ``robot.q = ...`` checks and sets the joint configuration

        .. note::  ???
        """
        return self._q

    @q.setter
    def q(self, q_new):
        self._q = getvector(q_new, self.n)
# --------------------------------------------------------------------- #

    @property
    def qd(self):
        """
        Get/set robot joint velocity

        - ``robot.qd`` is the robot joint velocity

        :return: robot joint velocity
        :rtype: ndarray(n,)

        - ``robot.qd = ...`` checks and sets the joint velocity

        .. note::  ???
        """
        return self._qd

    @qd.setter
    def qd(self, qd_new):
        self._qd = getvector(qd_new, self.n)
# --------------------------------------------------------------------- #

    @property
    def qdd(self):
        """
        Get/set robot joint acceleration

        - ``robot.qdd`` is the robot joint acceleration

        :return: robot joint acceleration
        :rtype: ndarray(n,)

        - ``robot.qdd = ...`` checks and sets the robot joint acceleration

        .. note::  ???
        """
        return self._qdd
    @qdd.setter
    def qdd(self, qdd_new):
        self._qdd = getvector(qdd_new, self.n)
# --------------------------------------------------------------------- #

# TODO could we change this to control_mode ?
    @property
    def control_type(self):
        """
        Get/set robot control mode

        - ``robot.control_type`` is the robot control mode

        :return: robot control mode
        :rtype: ndarray(n,)

        - ``robot.control_type = ...`` checks and sets the robot control mode

        .. note::  ???
        """
        return self._control_type

    @control_type.setter
    def control_type(self, cn):
        if cn == 'p' or cn == 'v' or cn == 'a':
            self._control_type = cn
        else:
            raise ValueError(
                'Control type must be one of \'p\', \'v\', or \'a\'')

    def ikcon(self, T, q0=None):
        """
        Inverse kinematics by optimization with joint limits

        q, success, err = ikcon(T, q0) calculates the joint coordinates (1xn)
        corresponding to the robot end-effector pose T which is an SE3 object
        or homogenenous transform matrix (4x4), and N is the number of robot
        joints. Initial joint coordinates Q0 used for the minimisation.

        q, success, err = ikcon(T) as above but q0 is set to 0.

        Trajectory operation:
        In all cases if T is a vector of SE3 objects or a homogeneous
        transform sequence (4x4xm) then returns the joint coordinates
        corresponding to each of the transforms in the sequence. q is mxn
        where n is the number of robot joints. The initial estimate of q
        for each time step is taken as the solution from the previous time
        step. Retruns trajectory of joints q (mxn), list of success (m) and
        list of errors (m)

        :param T: The desired end-effector pose
        :type T: SE3 or SE3 trajectory
        :param q0: initial joint configuration (default all zeros)
        :type q0: float ndarray(n) (default all zeros)

        :retrun q: The calculated joint values
        :rtype q: float ndarray(n)
        :retrun success: IK solved (True) or failed (False)
        :rtype success: bool
        :retrun error: Final pose error
        :rtype error: float

        :notes:
            - Joint limits are considered in this solution.
            - Can be used for robots with arbitrary degrees of freedom.
            - In the case of multiple feasible solutions, the solution
              returned depends on the initial choice of q0.
            - Works by minimizing the error between the forward kinematics
              of the joint angle solution and the end-effector frame as an
              optimisation.
            - The objective function (error) is described as:
              sumsqr( (inv(T)*robot.fkine(q) - eye(4)) * omega )
              Where omega is some gain matrix, currently not modifiable.

        """

        if not isinstance(T, SE3):
            T = SE3(T)

        trajn = len(T)

        try:
            if q0 is not None:
                q0 = getvector(q0, self.n, 'row')
            else:
                q0 = np.zeros((trajn, self.n))
        except ValueError:
            verifymatrix(q0, (trajn, self.n))

        # create output variables
        qstar = np.zeros((trajn, self.n))
        error = []
        exitflag = []

        omega = np.diag([1, 1, 1, 3 / self.reach])

        def cost(q, T, omega):
            return np.sum(
                (
                    (np.linalg.pinv(T.A) @ self.fkine(q).A - np.eye(4)) @
                    omega) ** 2
            )

        bnds = Bounds(self.qlim[0, :], self.qlim[1, :])

        for i in range(trajn):
            Ti = T[i]
            res = minimize(
                lambda q: cost(q, Ti, omega),
                q0[i, :], bounds=bnds, options={'gtol': 1e-6})
            qstar[i, :] = res.x
            error.append(res.fun)
            exitflag.append(res.success)

        if trajn > 1:
            return qstar, exitflag, error
        else:
            return qstar[0, :], exitflag[0], error[0]

    def ikine(
            self, T,
            ilimit=500,
            rlimit=100,
            tol=1e-10,
            Y=0.1,
            Ymin=0,
            mask=None,
            q0=None,
            search=False,
            slimit=100,
            transpose=None):
        """
        Inverse kinematics by optimization without joint limits

        ``q, failure, reason = ikine(T)`` are the joint coordinates (n)
        corresponding to the robot end-effector pose ``T`` which is an ``SE3``
        instance. ``failure`` is True if the solver failed, and ``reason``
        contains details of the failure.

        This method can be used for robots with any number of degrees of
        freedom.

        Trajectory operation:
        If ``T`` contains multiple values, ie. a trajectory, then returns the
        joint coordinates corresponding to each of the pose values in ``T``.
        ``q`` is mxn where n is the number of robot joints. The initial
        estimate of ``q`` for each time step is taken as the solution from the
        previous time step. Returns trajectory of joints ``q`` (mxn), list of
        failure (m) and list of error reasons (m).

        :param T: The desired end-effector pose
        :type T: SE3 or SE3 trajectory
        :param ilimit: maximum number of iterations
        :type ilimit: int (default 500)
        :param rlimit: maximum number of consecutive step rejections
        :type rlimit: int (default 100)
        :param tol: final error tolerance
        :type tol: float (default 1e-10)
        :param Y: initial value of lambda
        :type Y: float (default 0.1)
        :param Ymin: minimum allowable value of lambda
        :type Ymin: float (default 0)
        :param mask: mask vector that correspond to translation in X, Y and Z
            and rotation about X, Y and Z respectively.
        :type mask: float ndarray(6)
        :param q0: initial joint configuration (default all zeros)
        :type q0: float ndarray(n) (default all zeros)
        :param search: search over all configurations
        :type search: bool
        :param slimit: maximum number of search attempts
        :type slimit: int (default 100)
        :param transpose: use Jacobian transpose with step size A, rather
            than Levenberg-Marquadt
        :type transpose: float

        :return q: The calculated joint values
        :rtype q: float ndarray(n)
        :return failure: IK solver failed
        :rtype failure: bool or list of bool
        :return error: If failed, what went wrong
        :rtype error: List of str

        Underactuated robots:
        For the case where the manipulator has fewer than 6 DOF the
        solution space has more dimensions than can be spanned by the
        manipulator joint coordinates.

        In this case we specify the 'mask' option where the mask vector (1x6)
        specifies the Cartesian DOF (in the wrist coordinate frame) that will
        be ignored in reaching a solution.  The mask vector has six elements
        that correspond to translation in X, Y and Z, and rotation about X, Y
        and Z respectively. The value should be 0 (for ignore) or 1. The
        number of non-zero elements should equal the number of manipulator
        DOF.

        For example when using a 3 DOF manipulator rotation orientation might
        be unimportant in which case use the option: mask = [1 1 1 0 0 0].

        For robots with 4 or 5 DOF this method is very difficult to use since
        orientation is specified by T in world coordinates and the achievable
        orientations are a function of the tool position.

        :notes:
            - Solution is computed iteratively.
            - Implements a Levenberg-Marquadt variable step size solver.
            - The tolerance is computed on the norm of the error between
              current and desired tool pose.  This norm is computed from
              distances and angles without any kind of weighting.
            - The inverse kinematic solution is generally not unique, and
              depends on the initial guess q0 (defaults to 0).
            - The default value of q0 is zero which is a poor choice for most
              manipulators (eg. puma560, twolink) since it corresponds to a
              kinematic singularity.
            - Such a solution is completely general, though much less
              efficient than specific inverse kinematic solutions derived
              symbolically, like ikine6s or ikine3.
            - This approach allows a solution to be obtained at a singularity,
              but the joint angles within the null space are arbitrarily
              assigned.
            - Joint offsets, if defined, are added to the inverse kinematics
              to generate q.
            - Joint limits are not considered in this solution.
            - The 'search' option peforms a brute-force search with initial
              conditions chosen from the entire configuration space.
            - If the search option is used any prismatic joint must have
              joint limits defined.

        :references:
            - Robotics, Vision & Control, P. Corke, Springer 2011,
              Section 8.4.

        """

        if not isinstance(T, SE3):
            T = SE3(T)

        trajn = len(T)
        err = []

        try:
            if q0 is not None:
                if trajn == 1:
                    q0 = getvector(q0, self.n, 'row')
                else:
                    verifymatrix(q0, (trajn, self.n))
            else:
                q0 = np.zeros((trajn, self.n))
        except ValueError:
            verifymatrix(q0, (trajn, self.n))

        if mask is not None:
            mask = getvector(mask, 6)
        else:
            mask = np.ones(6)

        if search:
            # Randomised search for a starting point
            search = False
            # quiet = True

            for k in range(slimit):

                q0n = np.zeros(self.n)
                for j in range(self.n):
                    qlim = self.links[j].qlim
                    if np.sum(np.abs(qlim)) == 0:
                        if not self.links[j].sigma:
                            q0n[j] = np.random.rand() * 2 * np.pi - np.pi
                        else:
                            raise ValueError('For a prismatic joint, '
                                             'search requires joint limits')
                    else:
                        q0n[j] = np.random.rand() * (qlim[1] - qlim[0]) + \
                            qlim[0]

                # fprintf('Trying q = %s\n', num2str(q))

                q, _, _ = self.ikine(
                    T,
                    ilimit,
                    rlimit,
                    tol,
                    Y,
                    Ymin,
                    mask,
                    q0n,
                    search,
                    slimit,
                    transpose)

                if not np.sum(np.abs(q)) == 0:
                    return q, True, err

            q = np.array([])
            return q, False, err

        if not self.n >= np.sum(mask):
            raise ValueError('Number of robot DOF must be >= the same number '
                             'of 1s in the mask matrix')
        W = np.diag(mask)

        # Preallocate space for results
        qt = np.zeros((len(T), self.n))

        # Total iteration count
        tcount = 0

        # Rejected step count
        rejcount = 0

        failed = []
        nm = 0

        revolutes = []
        for i in range(self.n):
            revolutes.append(not self.links[i].sigma)

        for i in range(len(T)):
            iterations = 0
            q = np.copy(q0[i, :])
            Yl = Y

            while True:
                # Update the count and test against iteration limit
                iterations += 1

                if iterations > ilimit:
                    err.append('ikine: iteration limit {0} exceeded '
                               ' (pose {1}), final err {2}'.format(
                                   ilimit, i, nm))
                    failed.append(True)
                    break

                e = tr2delta(self.fkine(q).A, T[i].A)

                # Are we there yet
                if np.linalg.norm(W @ e) < tol:
                    # print(iterations)
                    failed.append(False)
                    break

                # Compute the Jacobian
                J = self.jacobe(q)

                JtJ = J.T @ W @ J

                if transpose is not None:
                    # Do the simple Jacobian transpose with constant gain
                    dq = transpose * J.T @ e
                else:
                    # Do the damped inverse Gauss-Newton with
                    # Levenberg-Marquadt
                    dq = np.linalg.inv(
                        JtJ + ((Yl + Ymin) * np.eye(self.n))
                    ) @ J.T @ W @ e

                    # Compute possible new value of
                    qnew = q + dq

                    # And figure out the new error
                    enew = tr2delta(self.fkine(qnew).A, T[i].A)

                    # Was it a good update?
                    if np.linalg.norm(W @ enew) < np.linalg.norm(W @ e):
                        # Step is accepted
                        q = qnew
                        e = enew
                        Yl = Yl / 2
                        rejcount = 0
                    else:
                        # Step is rejected, increase the damping and retry
                        Yl = Yl * 2
                        rejcount += 1
                        if rejcount > rlimit:
                            err.append(
                                'ikine: rejected-step limit {0} exceeded '
                                '(pose {1}), final err {2}'.format(
                                    rlimit, i, np.linalg.norm(W @ enew)))
                            failed.append(True)
                            break

                # Wrap angles for revolute joints
                k = (q > np.pi) & revolutes
                q[k] -= 2 * np.pi

                k = (q < -np.pi) & revolutes
                q[k] += + 2 * np.pi

                nm = np.linalg.norm(W @ e)

            qt[i, :] = q
            tcount += iterations

        if any(failed):
            err.append(
                'failed to converge: try a different '
                'initial value of joint coordinates')

        if trajn == 1:
            qt = qt[0, :]
            failed = failed[0]

        return qt, failed, err

    def ikunc(self, T, q0=None, ilimit=1000):
        """
        Inverse manipulator by optimization without joint limits

        q, success, err = ikunc(T) are the joint coordinates (n) corresponding
        to the robot end-effector pose T which is an SE3 object or
        homogenenous transform matrix (4x4), and n is the number of robot
        joints. Also returns success and err which is the scalar final value
        of the objective function.

        q, success, err = robot.ikunc(T, q0, ilimit) as above but specify the
        initial joint coordinates q0 used for the minimisation.

        Trajectory operation:
        In all cases if T is a vector of SE3 objects (m) or a homogeneous
        transform sequence (4x4xm) then returns the joint coordinates
        corresponding to each of the transforms in the sequence. q is mxn
        where n is the number of robot joints. The initial estimate of q
        for each time step is taken as the solution from the previous time
        step.

        :param T: The desired end-effector pose
        :type T: SE3 or SE3 trajectory
        :param ilimit: Iteration limit (default 1000)
        :type ilimit: bool

        :retrun q: The calculated joint values
        :rtype q: float ndarray(n)
        :retrun success: IK solved (True) or failed (False)
        :rtype success: bool
        :retrun error: Final pose error
        :rtype error: float

        :notes:
            - Joint limits are not considered in this solution.
            - Can be used for robots with arbitrary degrees of freedom.
            - In the case of multiple feasible solutions, the solution
              returned depends on the initial choice of q0
            - Works by minimizing the error between the forward kinematics of
              the joint angle solution and the end-effector frame as an
              optimisation.
            - The objective function (error) is described as:
              sumsqr( (inv(T)*robot.fkine(q) - eye(4)) * omega )
              Where omega is some gain matrix, currently not modifiable.

        """

        if not isinstance(T, SE3):
            T = SE3(T)

        trajn = len(T)

        if q0 is None:
            q0 = np.zeros((trajn, self.n))

        verifymatrix(q0, (trajn, self.n))

        qt = np.zeros((trajn, self.n))
        success = []
        err = []

        omega = np.diag([1, 1, 1, 3 / self.reach])

        def sumsqr(arr):
            return np.sum(np.power(arr, 2))

        for i in range(trajn):

            Ti = T[i]

            res = minimize(
                lambda q: sumsqr(((
                    np.linalg.inv(Ti.A) @ self.fkine(q).A) - np.eye(4)) @
                    omega),
                q0[i, :],
                options={'gtol': 1e-6, 'maxiter': ilimit})

            qt[i, :] = res.x
            success.append(res.success)
            err.append(res.fun)

        if trajn == 1:
            return qt[0, :], success[0], err[0]
        else:
            return qt, success, err
