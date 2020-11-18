#!/usr/bin/env python
"""
@author Jesse Haviland
"""

import roboticstoolbox as rtb

# Launch the simulator Swift
env = rtb.backends.Swift()
env.launch()

# Create a Panda robot object
robot = rtb.models.Puma560()
env.add(robot)

env.hold()

# print(panda)
# print(panda.base_link)
# print(panda.ee_links)

# path, n = panda.get_path(panda.base_link, panda.ee_links[0])

# q1 = np.array([1.4, 0.2, 1.8, 0.7, 0.1, 3.1, 2.9])
# panda.q = q1

# print(panda.fkine())

# for link in path:
#     print(link.name)

# print(panda.get_path(panda.base_link, panda.ee_links[0])[0])

# print(panda.links[5].A(0))

# # Set joint angles to ready configuration
# panda.q = panda.qr

# Add the Panda to the simulator
# env.add(panda)


# while 1:
#     pass
