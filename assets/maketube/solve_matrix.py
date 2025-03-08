import numpy as np
import matplotlib.pyplot as plt

XS = 0
XE = 1
NUM_POINTS = 100
R_MAX = 2
R_MIN = 0.5

z = np.linspace(XS, XE, NUM_POINTS)

A  =   np.array([
[1,     XS,         XS**2,         XS**3,           XS**4,          XS**5            ],
[1,     XE,         XE**2,         XE**3,           XE**4,          XE**5            ],
[0,     1,          2*XS,          3*XS**2,         4*XS**3,        5*XS**4          ],
[0,     1,          2*XE,          3*XE**2,         4*XE**3,        5*XE**4          ],
[1,     (XE+XS)/2,  (XE+XS)**2/4,  (XE+XS)**3/8,    (XE+XS)**4/16,  (XE+XS)**5/32    ],
[0,     1,          XE+XS,         3*(XE+XS)**2/4,  (XE+XS)**3/2,   5*(XE+XS)**4/16  ]
])

B = np.array([R_MAX, R_MAX, 0.0, 0.0, R_MIN, 0.0])

X = np.linalg.solve(A, B)

radius = X[0] + X[1]*z + X[2]*z**2 + X[3]*z**3 + X[4]*z**4 + X[5]*z**5

print(X)

plt.figure(figsize=(8, 6))
plt.plot(z, radius, label="Radius vs z", color='b')
plt.xlabel("z")
plt.ylabel("radius")
plt.title("Radius as a function of z")
plt.legend()
plt.grid(True)
plt.savefig("radius_plot.png", dpi=300)
plt.show()