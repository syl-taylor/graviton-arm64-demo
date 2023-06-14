import numpy as np
from sklearn.tree import DecisionTreeRegressor
import matplotlib.pyplot as plt

# Create random dataset
rng = np.random.RandomState(1)
X = np.sort(5 * rng.rand(100, 1), axis=0)
y = np.sin(X).ravel()
y[::5] += 3 * (0.5 - rng.rand(32))

# Fit regression model
dtreg_1 = DecisionTreeRegressor(max_depth=2)
dtreg_2 = DecisionTreeRegressor(max_depth=5)
dtreg_1.fit(X, y)
dtreg_2.fit(X, y)

# Predict
X_test = np.arange(0.0, 5.0, 0.01)[:, np.newaxis]
y_1 = regr_1.predict(X_test)
y_2 = regr_2.predict(X_test)

# Plot results
plt.figure()
plt.scatter(X, y, s=20, edgecolor="black", c="orange", label="data")
plt.plot(X_test, y_1, color="blue", label="max_depth=2", linewidth=2)
plt.plot(X_test, y_2, color="green", label="max_depth=5", linewidth=2)
plt.xlabel("data")
plt.ylabel("target")
plt.title("Decision Tree Regression")
plt.legend()
plt.savefig("plot.png")
