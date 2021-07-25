"""
Python Navigation Abstract Class
@Author: Kristian Gibson
TODO: Comments + Sphynx Docs Structured Text
TODO: Bug-fix, testing

Not ready for use yet.
"""
from scipy import integrate
from spatialmath.base.transforms2d import *
from spatialmath.base.vectors import *
from spatialmath import SE2, SE3
from matplotlib import cm
from abc import ABC, abstractmethod
import matplotlib as mpl
import matplotlib.pyplot as plt
import copy
from roboticstoolbox.mobile.OccGrid import BinaryOccupancyGrid
from colored import fg, attr

class Planner:
    r"""
    Mobile robot motion planner (superclass)

    :param occgrid: occupancy grid, defaults to None
    :type occgrid: :class:`OccGrid` instance of ndarray(N,M), optional
    :param start: start position :math:`(x, y)` or configuration :math:`(x, y, \theta)`, defaults to None
    :type start: array_like(2) or array_like(3), optional
    :param goal: goal position :math:`(x, y)` or configuration :math:`(x, y, \theta)`, defaults to None
    :type goal: array_like(2) or array_like(3), optional
    :param inflate: obstacle inflation, defaults to 0
    :type inflate: float, optional
    :param ndims: dimensionality of the planning, either 2 for :math:`\mathbb{R}^2` or 
        3 for :math:`\SE{2}`
    :param ndims: int, optional
    :param verbose: verbosity, defaults to False
    :type verbose: bool, optional
    :param msgcolor: color for message channel printing
    :type msgcolor: str, defaults to yellow
    :param seed: seed provided to private random number generator, defaults to None
    :type seed: int, optional

    Superclass for all mobile robot motion planners.  Key functionality
    includes:

    - encapsulates an occupancy grid and optionally inflates it
    - encapsulates a private random number generator with specifiable seed
    - encapsulates state such as start, goal, and the plan
    - provides a message channel for diagnostic output

    :seealso: :class:`OccGrid`
    """

    def __init__(self, occgrid=None, inflate=0, ndims=None,
                 verbose=False, msgcolor='yellow', seed=None, **unused):

        self._occgrid = None
        if ndims is None:
            raise ValueError('ndims must be specified')
        self._ndims = ndims
        self._verbose = verbose
        self._msgcolor = msgcolor
        self._seed = seed
        self._private_random = np.random.default_rng(seed=seed)
        self._inflate = inflate
        self._start = None
        self._goal = None

        if occgrid is not None:
            if not isinstance(occgrid, BinaryOccupancyGrid):
                occgrid = BinaryOccupancyGrid(occgrid)
            self._occgrid0 = occgrid  # original occgrid for reference

            if inflate > 0:
                self._occgrid = occgrid.copy()
                self._occgrid.inflate(inflate)
            else:
                self._occgrid = occgrid

    def __str__(self):
        """
        Compact representation of the planner

        :return: pretty printed representation
        :rtype: str
        """
        s = f"{self.__class__.__name__}: "
        if self._occgrid0 is not None:
            s += str(self.occgrid)
        if self._start is not None:
            s += f"\n Start: {self.start}"
        if self._goal is not None:
            s += f"\n  Goal: {self.goal}"
        return s

    @property
    def occgrid(self):
        """
        Occupancy grid

        :return: occupancy grid used for planning
        :rtype: :class:`OccGrid` instance or None

        Returns the grid that was optionally inflated at constructor time.

        :seealso: :class:`OccGrid`
        """
        return self._occgrid

    @property
    def start(self):
        r"""
        Start point or configuration used for planning

        :return: start point :math:`(x, y)` or configuration :math:`(x, y, \theta)`
        :rtype: ndarray(2) or ndarray(3)
        """
        return self._start

    @start.setter
    def start(self, start):
        r"""
        Set start point or configuration for planning

        :param start: Set start :math:`(x, y)` or configuration :math:`(x, y, \theta)`
        :type start: array_like(2) or array_like(3)
        :raises ValueError: if start point is occupied
        """
        if start is not None:
            if self.isoccupied(start):
                raise ValueError("Start location inside obstacle")
            self._start = base.getvector(start)

    @property
    def goal(self):
        r"""
        Goal point or configuration used for planning

        :return: goal point :math:`(x, y)` or configuration :math:`(x, y, \theta)`
        :rtype: ndarray(2) or ndarray(3)
        """
        return self._goal

    @goal.setter
    def goal(self, goal):
        r"""
        Set goal point or configuration for planning

        :param goal: Set goal :math:`(x, y)` or configuration :math:`(x, y, \theta)`
        :type goal: array_like(2) or array_like(3)
        :raises ValueError: if goal point is occupied
        """
        if goal is not None:
            if self.isoccupied(goal):
                raise ValueError("Goal location inside obstacle")
            self._goal = base.getvector(goal)

    def isoccupied(self, p):
        """
        Test if point is occupied

        :param p: world coordinate (x, y)
        :type p: array_like(2)
        :return: occupancy status of corresponding grid cell
        :rtype: bool

        The world coordinate is transformed and the status of the occupancy
        grid cell is returned.  If the point lies outside the bounds of
        the occupancy grid return True (obstacle)

        If there is no occupancy grid this function always returns False (free).

        :seealso: :meth:`OccGrid.isoccupied`
        """
        if self.occgrid is None:
            return False
        else:
            return self.occgrid.isoccupied(p)

    @property
    def verbose(self):
        """
        Get verbosity

        :return: verbosity
        :rtype: bool

        If ``verbosity`` print more diagnostic messages to the planner's
        message channel.
        """
        return self._verbose

    @verbose.setter
    def verbose(self, v):
        """
        Set verbosity

        :param v: verbosity
        :type v: bool

        If ``verbosity`` print more diagnostic messages to the planner's
        message channel.
        """
        self._verbose = v

    @property
    def random(self):
        """
        Private random number generator

        :return: random number generator
        :rtype: NumPy Generator

        For example::

            planner.random(size, dtype)
            planner.integers(low, high, size, dtype)
            planner.uniform(0, 5)
       
        :seealso: `Random Generator <https://numpy.org/doc/stable/reference/random/generator.html>`_
        """
        return self._private_random


    # Define abstract classes to be implemented later
    @abstractmethod
    def plan(self):
        r"""
        Plan path (abstract superclass)

        :param start: start position :math:`(x, y)` or configuration :math:`(x, y, \theta)`, defaults to None
        :type start: array_like(2) or array_like(3), optional
        :param goal: goal position :math:`(x, y)` or configuration :math:`(x, y, \theta)`, defaults to None
        :type goal: array_like(2) or array_like(3), optional

        The implementation depends on the particular planner.  Some may have
        no planning phase.  The plan may also depend on just the start or goal.
        """
        pass

    def validate_endpoint(self, p, dtype=None):
        if p is not None:
            p = base.getvector(p, self._ndims, dtype=dtype)
            if self.isoccupied(p):
                raise ValueError("Point is inside obstacle")
        return p

    def query(self, start=None, goal=None, dtype=None, next=True, animate=False, movie=None):
        """
        Find a path from start to goal using plan (superclass)

        :param start: start position :math:`(x, y)` or configuration :math:`(x, y, \theta)`, defaults to None
        :type start: array_like(2) or array_like(3), optional
        :param goal: goal position :math:`(x, y)` or configuration :math:`(x, y, \theta)`, defaults to None
        :type goal: array_like(2) or array_like(3), optional
        :param animate: show the vehicle path, defaults to False
        :type animate: bool, optional
        :return: path from start to goal, one point :math:`(x, y)` or configuration :math:`(x, y, \theta)` per row
        :rtype: ndarray(N,2) or ndarray(N,3)

        Find a path from ``start`` to ``goal`` using a previously computed plan.
        
        The method performs the following steps:
        - Initialize navigation, invoke method N.navigate_init()
        - Visualize the environment, invoke method N.plot()
        - Iterate on the ``next()`` method of the subclass until the ``goal`` is
          achieved.
        """
        # make sure start and goal are set and valid
        self.start = self.validate_endpoint(start, dtype=dtype)
        self.goal = self.validate_endpoint(goal, dtype=dtype)

        # if movie is not None:
        #     animate = True

        if next:
            if animate:
                self.plot()

            # movie = MovieWriter(movie)

            robot = self._start
            path = [robot]

            while True:
                if animate:
                    plt.plot(robot[0], robot[1], 'y.', 12)
                    plt.pause(0.05)

                # get next point on the path
                robot = self.next(robot)

                # are we are done?
                if robot is None:
                    path.append(self._goal)
                    return np.array(path).astype(int)

                path.append(robot)

    def plot(self, path=None,
            direction=None, background=True,
            twod=False, unwrap=True,
            path_marker=None, path_marker_reverse=None,
            start_marker=None, goal_marker=None,
            qstart_marker=None, qgoal_marker=None,
            start=None, goal=None,
            ax=None, block=False, **kwargs):
        r"""
        Plot vehicle path

        :param path: path, defaults to None
        :type p: ndarray(N,2) or ndarray(N,3)
        :param direction: travel direction associated with each point on path, is either >0 or <0, defaults to None
        :type direction: ndarray(N,), optional
        :param twod: for configuration space paths force a 2D plot but 
            start and goal style will be given by ``qstart_marker`` and ``qgoal_marker``, defaults to False
        :type twod: bool, optional
        :param unwrap: for configuration space plot unwrap :math:`\theta` so
            there are no discontinuities at :math:`\pm \pi`, defaults to True
        :type unwrap: bool, optional
        :param background: plot occupancy grid if present, default True
        :type background: bool, optional
        :param path_marker: style for marking points on path when travelling forward
        :type path_marker: dict, optional
        :param path_marker: style for marking points on path when travelling backward
        :type path_marker: dict, optional
        :param start_marker: style for marking start point
        :type start_marker: dict, optional
        :param goal_marker: style for marking goal point
        :type goal_marker: dict, optional
        :param qstart_marker: style for marking start configuration in 2D plane
        :type qstart_marker: dict, optional
        :param qgoal_marker: style for marking goal configuration in 2D plane
        :type qgoal_marker: dict, optional
        :param start: start position :math:`(x, y)` or configuration :math:`(x, y, \theta)`, defaults to value used for ``plan/query``
        :type start: array_like(2) or array_like(3), optional
        :param goal: goal position :math:`(x, y)` or configuration :math:`(x, y, \theta)`, defaults to value used for ``plan/query``
        :type goal: array_like(2) or array_like(3), optional
        :param ax: axes to plot into
        :type ax: matplotlib axes
        :param block: block after displaying the plot
        :type block: bool, optional

        The path has one row per time step and either 2 or 3 columns:
        
        - 2 columns describes motion in the :math:`x-y` plane and a 2D plot  is created
        - 3 columns describes motion in the :math:`x-y-\theta` configuration space and
          a 3D plot is created unless ``twod`` is True in which case motion in
          the :math:`x-y` plane is shown.

        Markers are specified as dicts using Matplotlib keywords, for example::

            planner.plot(path, path_marker=dict(marker='s', color='b'))

        Default values are provided for all markers:

            - forward motion is a blue dot,
            - backward motion is a red dot,
            - the start point is a circle, and
            - the goal point is a star. 
    
        If ``twod`` is True then direction-indicating markers are used to
        display start and goal configuration. These are also given as dicts but
        have two items: ``'shape'`` which is the shape of the polygonal marker
        and is either ``'triangle'`` or ``'car'``.  The second item ``'args'`` is
        passed to :func:`base.plot_poly` and Matplotlib.

        If the planner supports bi-directional motion then the ``direction``
        option gives the direction for each point on the path.

        If ``background`` is True then the background of the plot is either or
        both of:
        
        - the occupancy grid
        - the distance field of the planner

        Additional arguments are passed through to :meth:`plot_bg`

        :seealso: :meth:`plot_bg` :func:`base.plot_poly`
        """
        # create default markers
        if path_marker is None:
            path_marker = { 'marker': '.',
                            'markerfacecolor': 'b',
                            'markersize': 12,
                          }
            path_marker_reverse = { 'marker': '.',
                            'markerfacecolor': 'r',
                            'markersize': 10,
                          }
        if start_marker is None:
            start_marker = {'marker': 'o',
                            'markeredgecolor': 'w',
                            'markerfacecolor': 'y', 
                            'markersize': 10,
                            'zorder': 10,
                           }
        if goal_marker is None:
            goal_marker = { 'marker': '*',
                            'markeredgecolor': 'w',
                            'markerfacecolor': 'y',
                            'markersize': 16,
                            'zorder': 10,
                          }
        if qstart_marker is None:
            qstart_marker = {'shape': 'triangle',
                             'args': {
                                'linewidth': 2,
                                'color': 'darkgrey',
                                }
                            }
        if qgoal_marker is None:
            qgoal_marker = {'shape': 'triangle',
                             'args': {
                                'filled': True,
                                'color': 'darkgrey'
                                }
                            }

        ndims = self._ndims
        if twod:
            if path is not None:
                path0 = path
                path = path[:, :2]
                ndims = 2

        ax = base.axes_logic(ax, ndims)

        # plot occupancy grid background
        if background:
            self.plot_bg(ax=ax, **kwargs)
        
        # mark the path
        if path is not None:
            if ndims == 2:
                # 2D case
                if direction is not None:
                    direction = np.array(direction)
                    if direction.shape[0] != path.shape[0]:
                        raise ValueError('direction vector must have same length as path')
                    ax.plot(path[:, 0], path[:, 1], 'k')
                    ax.plot(path[direction > 0, 0], path[direction > 0, 1], color='none', **path_marker)
                    ax.plot(path[direction < 0, 0], path[direction < 0, 1], color='none', **path_marker_reverse)
                else:
                    ax.plot(path[:, 0], path[:, 1], **path_marker)
            elif ndims == 3:
                # 3D case
                if direction is not None:
                    direction = np.array(direction)
                    if direction.shape[0] != path.shape[0]:
                        raise ValueError('direction vector must have same length as path')
                    theta = path[:, 2]
                    if unwrap:
                        theta = np.unwrap(path[:, 2])
                    ax.plot(path[:, 0], path[:, 1], theta, 'k')
                    ax.plot(path[direction > 0, 0], path[direction > 0, 1], theta[direction > 0], color='none', **path_marker)
                    ax.plot(path[direction < 0, 0], path[direction < 0, 1], theta[direction < 0], color='none', **path_marker_reverse)
                else:
                    theta = path[:, 2]
                    if unwrap:
                        theta = np.unwrap(path[:, 2])
                    ax.plot(path[:, 0], path[:, 1], theta, **path_marker)

        # mark start and goal if requested
        if start is not None:
            start = self.validate_endpoint(start)
        else:
            start = self.start
        if goal is not None:
            self.goal = self.validate_endpoint(goal)
        else:
            goal = self.goal

        if ndims == 2 and not twod:
            # proper 2d plot
            if start is not None:
                ax.plot(start[0], start[1], **start_marker)
            if goal is not None:
                ax.plot(goal[0], goal[1], **goal_marker)
        
        elif ndims == 2 and twod:
            # 2d projection of 3d plot, show start/goal configuration
            scale = base.axes_get_scale(ax) / 10

            if start is not None:
                poly = self._qmarker(qstart_marker['shape']) * scale
                base.plot_poly(poly, pose=SE2(start), **qstart_marker['args'])
            if goal is not None:
                poly = self._qmarker(qgoal_marker['shape']) * scale
                base.plot_poly(poly, pose=SE2(goal), **qgoal_marker['args'])

        elif ndims == 3:
            # 3d plot

            if start is not None:
                ax.plot(start[0], start[1], start[2], **start_marker)
            if goal is not None:
                
                if path is not None and unwrap:
                    theta = theta[-1]
                else:
                    theta = goal[2]
                plt.plot(goal[0], goal[1], theta, **goal_marker)

        ax.set_xlabel('x')
        ax.set_ylabel('y')
        if ndims == 2:
            ax.set_aspect('equal')
        else:
            ax.set_zlabel(r'$\theta$')

        plt.show(block=block)

    def _qmarker(self, shape):
        h = 0.3
        t = 0.8  # start of head taper
        c = 0.5  # centre x coordinate
        w = 1    # width in x direction
        if shape == 'car':
            return np.array([
                [-c,     h],
                [t - c,  h],
                [w - c,  0],
                [t - c, -h],
                [-c,    -h],
            ]).T
        elif shape == 'triangle':
            return np.array([
                [-c,  h],
                [ w,  0],
                [-c, -h],
                [-c,  h],
            ]).T

    def plot_bg(self, distance=None, cmap='gray',
                ax=None, inflated=True,  **unused):
        """
        Plot background

        :param distance: override distance field, defaults to None
        :type distance: ndarray(N,M), optional
        :param cmap: Specify a colormap for the distance field, defaults to 'gray'
        :type cmap: str or Colormap, optional

        Displays the background which is either the occupancy grid or a distance
        field.  The distance field encodes the distance of a point from the goal, small
        distance is dark, a large distance is bright.

        If the planner has an occupancy grid then that will be displayed with:
            - free cells in white
            - occupied cells in red
            - inflated occupied cells in pink

        If distance is provided, or the planner has a distancemap attribute
        the the distance field will be used as the background and obstacle cells
        (actual or inflated) will be shown in red. A colorbar is added.
        """
        if self._occgrid is None:
            return

        ax = base.axes_logic(ax, 2)

        if distance is None and hasattr(self, 'distancemap'):
            distance = self.distancemap

        if distance is not None:
            # distance field with obstacles

            # find largest finite value

            v = distance.ravel()
            vmax = max(v[np.isfinite(v)])

            # create a copy of greyscale color map
            c_map = copy.copy(mpl.cm.get_cmap(cmap))
            c_map.set_bad(color=(1,0,0,1))  # nan and inf are red

            # change all inf to large value, so they are not 'bad' ie. red
            distance[np.isinf(distance)] = 2 * vmax
            c_map.set_over(color=(0,0,1))  # ex-infs are now blue

            # display image
            norm = mpl.colors.Normalize(vmin=0, vmax=vmax, clip=False)
            ax.imshow(distance, origin='lower',
                cmap=c_map,
                norm=norm,
                )
            ax.grid(True, alpha=0.1, color=(1,1,1))

            # add colorbar
            scalar_mappable_c_map = cm.ScalarMappable(cmap=c_map, norm=norm)
            plt.colorbar(scalar_mappable_c_map, label='Distance', shrink=0.7, aspect=20*0.7)

            ax.set_xlabel('X')
            ax.set_ylabel('y (cells)')

        else:
            # occupancy grid only

            # create color map for free space + obstacle:
            #   free space, color index = 1, white, alpha=0 to allow background and grid lines to show
            #   obstacle, color index = 2, red, alpha=1

            if self._inflate > 0 and inflated:
                # 0 background (white, transparent)
                # 1 inflated obstacle (pink)
                # 2 original obstacle (red)
                colors = [(1, 1, 1, 0), (1, 0.75, 0.8, 1), (1, 0, 0, 1)]
                image = self.occgrid.grid.astype(int) + self._occgrid0.grid.astype(int)
            else:
                # 0 background
                # 1 obstacle
                colors = [(1, 1, 1, 0), (1, 0, 0, 1)]
                image = self.occgrid.grid

            ax.set_facecolor((1, 1, 1)) # create white background
            c_map = mpl.colors.ListedColormap(colors)
            self.occgrid.plot(image, cmap=c_map, zorder=1)
            ax.grid(True, zorder=0)

        # lock axis limits to current value
        ax.set_xlim(ax.get_xlim())
        ax.set_ylim(ax.get_ylim())

        plt.draw()
        plt.show(block=False)


    def message(self, s, color=None):
        """
        Print message to message channel

        :param s: message to print
        :type s: str
        :param color: color to print it, defaults to color specified at
            constructor time.
        :type color: str, optional

        """
        if self.verbose:
            if color is None:
                color = self._msgcolor
            print(fg(color), "Planner:: " + s, attr(0))

    # @staticmethod
    # def show_distance(d):
    #     d[np.isinf(d)] = None
    #     ax = plt.gca()
    #     c_map = plt.get_cmap("Greys")
    #     plt.clim(0, np.max(d[:]))
    #     plt.figimage(d)
    #     plt.xlabel('X')
    #     plt.ylabel('Y')
    #     plt.show()

class MovieWriter:

    def __init__(self, filename=None, interval=0.1, fig=None):
        """
        Save animation as a movie file

        :param filename: name of movie file, or tuple containing filename and
            frame interval
        :type filename: str or tuple(str, float)
        :param interval: frame interval, defaults to 0.1
        :type interval: float, optional
        :param fig: figure to record for the movie
        :type fig: figure reference 

        Example::

            movie = MovieWriter(filename)

            while ...
                movie.add()

            movie.done()

        To avoid extra user-logic, if ``MovieWriter`` is called with ``filename`` equal to None,
        then the writer will do nothing when the ``add`` and ``done`` methods are called.
        """
        # Set up formatting for the movie files
        if filename is None:
            self.writer = None
            return

        if isinstance(filename, (tuple, list)):
            filename, interval = filename

        if os.path.exists(filename):
            print("overwriting movie", filename)
        else:
            print("creating movie", filename)
        self.writer = animation.FFMpegWriter(
            fps=round(1 / interval), extra_args=["-vcodec", "libx264"]
        )
        if fig is None:
            fig = plt.gcf()
        self.writer.setup(fig, filename)
        self.filename = filename

    def add(self):
        """
        Add frame to the movie
        """
        if self.writer is not None:
            self.writer.grab_frame()

    def done(self):
        if self.writer is not None:
            self.writer.finish()
            self.writer = None
