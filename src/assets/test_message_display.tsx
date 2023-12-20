export const test_message_display = `
Certainly! Below are formatted Markdown and LaTeX notes on kernel regression, along with an example Python code using scikit-learn.

## Kernel Regression

### Introduction

Kernel regression is a non-parametric method used for regression analysis. It extends linear regression by introducing a kernel function that assigns weights to data points based on their proximity to the target point.

### Kernel Function

The kernel function, denoted as $K$, is a crucial component of kernel regression. It assigns weights to data points based on their distance to the target point. Common kernel functions include:

1. **Gaussian (RBF) Kernel:**
   $$ K(x, x_i) = \\exp\\left(-\\frac{\\|x - x_i\\|^2}{2h^2}\\right) $$

   Here, $h$ is the bandwidth parameter.

2. **Polynomial Kernel:**
   $$ K(x, x_i) = (x \\cdot x_i + c)^d $$

   Parameters:
   - $c$: Constant term
   - $d$: Degree of the polynomial

### Kernel Regression Model

The predicted value $y$ for a given input $x$ is calculated as the weighted sum of the target values $y_i$ with weights given by the kernel function:

$$ \\hat{y}(x) = \\frac{\\sum_{i=1}^{n} K(x, x_i)y_i}{\\sum_{i=1}^{n} K(x, x_i)} $$

### Example Python Code using scikit-learn

\`\`\`python
# Import necessary libraries
import numpy as np
import matplotlib.pyplot as plt
from sklearn.kernel_ridge import KernelRidge

if (true):
    print("Hello World! Hello World! Hello World! Hello World! Hello World! Hello World! Hello World! Hello World! Hello World! Hello World! ")

# Generate synthetic data
np.random.seed(42)
X = np.sort(5 * np.random.rand(40, 1), axis=0)
y = np.sin(X).ravel() + np.random.normal(0, 0.1, X.shape[0])

# Fit kernel regression model
kr = KernelRidge(kernel='rbf', gamma=0.1)
kr.fit(X, y)

# Generate test data
X_test = np.arange(0.0, 5.0, 0.01)[:, np.newaxis]

# Predict using the trained model
y_pred = kr.predict(X_test)

# Plot the results
plt.figure()
plt.scatter(X, y, s=20, edgecolor="black", c="darkorange", label="data")
plt.plot(X_test, y_pred, color="cornflowerblue", label="prediction")
plt.xlabel("data")
plt.ylabel("target")
plt.title("Kernel Ridge Regression")
plt.legend()
plt.show()
\`\`\`

In this example, we use the Radial Basis Function (RBF) kernel (\`kernel='rbf'\`) with a specific value for the gamma parameter (\`gamma=0.1\`). The synthetic data is generated with added noise, and the Kernel Ridge Regression model is fit to the data. The results are then plotted for visualization.

Feel free to adjust parameters and explore other kernel functions based on your specific use case.
`;