# ORVEXA Astrodynamics Mathematics Documentation

This document outlines the core astrodynamics, coordinate frames, covariance transformations, and numerical integration mathematics utilized in the ORVEXA Space Situational Awareness (SSA) & Safety platform.

---

## 1. Coordinate Transformations: TEME to ECEF

SGP4 (Simplified General Perturbations 4) propagates orbital state vectors in the **True Equator Mean Equinox (TEME)** frame, which is a quasi-inertial coordinate system aligned with the Earth's true equator of date. For 3D visualization and geographical calculations, coordinates must be transformed into the **Earth-Centered Earth-Fixed (ECEF)** frame (specifically aligned with the WGS84 ellipsoid).

### Position Transformation
The transformation of the position vector $\mathbf{r}_{TEME} = [x, y, z]^T$ to the ECEF frame is a rotation about the Earth's spin axis ($Z$-axis) by the Greenwich Mean Sidereal Time (GMST) angle $\theta_{GMST}$:

$$\mathbf{r}_{ECEF} = \mathbf{R}_z(\theta_{GMST}) \mathbf{r}_{TEME}$$

where the rotation matrix $\mathbf{R}_z(\theta)$ is defined as:

$$\mathbf{R}_z(\theta) = \begin{bmatrix} \cos\theta & \sin\theta & 0 \\ -\sin\theta & \cos\theta & 0 \\ 0 & 0 & 1 \end{bmatrix}$$

### Velocity Transformation
Since the ECEF frame is rotating with the Earth at an angular velocity of $\boldsymbol{\omega}_e = [0, 0, \omega_e]^T$ (where $\omega_e \approx 7.292115 \times 10^{-5} \text{ rad/s}$), the velocity vector must account for Coriolis acceleration:

$$\mathbf{v}_{ECEF} = \mathbf{R}_z(\theta_{GMST}) \mathbf{v}_{TEME} - \boldsymbol{\omega}_e \times \mathbf{r}_{ECEF}$$

Or in matrix form:

$$\mathbf{v}_{ECEF} = \mathbf{R}_z(\theta_{GMST}) \mathbf{v}_{TEME} - \begin{bmatrix} -\omega_e y_{ECEF} \\ \omega_e x_{ECEF} \\ 0 \end{bmatrix}$$

---

## 2. B-Plane Covariance Projection & Foster-Elrod Math

During a close approach (conjunction), the 3D position uncertainties of the primary and secondary space objects are combined and projected onto the **Encounter Plane (B-plane)** perpendicular to the relative velocity vector at the Time of Closest Approach (TCA).

### B-Plane Coordinate Definition
Let $\mathbf{v}_{rel} = \mathbf{v}_p - \mathbf{v}_s$ be the relative velocity vector at TCA. The unit vector along the relative velocity is:

$$\hat{e}_z = \frac{\mathbf{v}_{rel}}{\|\mathbf{v}_{rel}\|}$$

We choose a reference direction (not parallel to $\hat{e}_z$) to define the orthogonal axes $\hat{e}_x$ and $\hat{e}_y$ that span the B-plane:

$$\hat{e}_x = \frac{\hat{e}_{ref} \times \hat{e}_z}{\|\hat{e}_{ref} \times \hat{e}_z\|}$$
$$\hat{e}_y = \hat{e}_z \times \hat{e}_x$$

The B-plane projection matrix $\mathbf{P}$ is a $2 \times 3$ matrix:

$$\mathbf{P} = \begin{bmatrix} \hat{e}_x^T \\ \hat{e}_y^T \end{bmatrix}$$

### Covariance Projection
The combined 3D positional covariance matrix $\mathbf{C}$ in the ECI frame is the sum of the primary and secondary covariance matrices:

$$\mathbf{C} = \mathbf{C}_p + \mathbf{C}_s$$

The projected 2D B-plane covariance matrix $\boldsymbol{\Sigma}_B$ is:

$$\boldsymbol{\Sigma}_B = \mathbf{P} \mathbf{C} \mathbf{P}^T = \begin{bmatrix} \hat{e}_x^T \mathbf{C} \hat{e}_x & \hat{e}_x^T \mathbf{C} \hat{e}_y \\ \hat{e}_y^T \mathbf{C} \hat{e}_x & \hat{e}_y^T \mathbf{C} \hat{e}_y \end{bmatrix}$$

### Diagonalization
We diagonalize $\boldsymbol{\Sigma}_B$ to find the principal standard deviations ($\sigma_x, \sigma_y$) and align the relative position vector $\mathbf{r}_B = [x_m, y_m]^T$ with the uncertainty ellipse axes:

$$\mathbf{r}_B' = \mathbf{R}_{diag}^T \mathbf{r}_B = [x_m', y_m']^T$$
$$\boldsymbol{\Sigma}_B' = \mathbf{R}_{diag}^T \boldsymbol{\Sigma}_B \mathbf{R}_{diag} = \begin{bmatrix} \sigma_x^2 & 0 \\ 0 & \sigma_y^2 \end{bmatrix}$$

### Probability of Collision ($P_c$)
Under the short-term encounter model, the probability of collision is the integral of the 2D Gaussian PDF over a circular area of radius $R$ (Hard Body Radius, `HBR`) representing the combined cross-section of both objects:

$$P_c = \frac{1}{2\pi \sigma_x \sigma_y} \iint_{x^2 + y^2 \leq R^2} \exp\left( -\frac{1}{2} \left[ \frac{(x - x_m')^2}{\sigma_x^2} + \frac{(y - y_m')^2}{\sigma_y^2} \right] \right) dx dy$$

Using Chan's analytical Rician Bessel series approximation:
- We define the equivalent isotropic standard deviation: $\sigma = \sqrt{\sigma_x \sigma_y}$.
- We define scaled distance parameters:
  $$\alpha = \sqrt{\frac{(x_m')^2}{\sigma_x^2} + \frac{(y_m')^2}{\sigma_y^2}}$$
  $$\beta = \frac{R}{\sigma}$$
- If $\beta \geq \alpha$, we expand $P_c$ as:
  $$P_c = 1 - e^{-\frac{(\alpha - \beta)^2}{2}} \sum_{k=0}^{\infty} \left( \frac{\alpha}{\beta} \right)^k \bar{I}_k(\alpha\beta)$$
- If $\alpha > \beta$, we expand $P_c$ as:
  $$P_c = e^{-\frac{(\alpha - \beta)^2}{2}} \sum_{k=1}^{\infty} \left( \frac{\beta}{\alpha} \right)^k \bar{I}_k(\alpha\beta)$$
where $\bar{I}_k(x) = e^{-x} I_k(x)$ is the exponentially scaled modified Bessel function of the first kind of order $k$, ensuring numerical stability.

---

## 3. Numerical Integration Scheme (Runge-Kutta 4th Order)

For low-altitude satellites experiencing reentry decay, the equations of motion must be integrated numerically under oblate gravity and atmospheric drag:

$$\frac{d}{dt} \begin{bmatrix} \mathbf{r} \\ \mathbf{v} \end{bmatrix} = \begin{bmatrix} \mathbf{v} \\ \mathbf{a}_g + \mathbf{a}_d \end{bmatrix}$$

### Gravitational Acceleration with J2 Perturbation
The acceleration $\mathbf{a}_g$ includes Newtonian gravity plus the oblate Earth perturbation ($J_2$):

$$\mathbf{a}_g = -\frac{\mu \mathbf{r}}{\|\mathbf{r}\|^3} + \frac{3 J_2 \mu R_E^2}{2 \|\mathbf{r}\|^5} \begin{bmatrix} x \left( 5 \frac{z^2}{\|\mathbf{r}\|^2} - 1 \right) \\ y \left( 5 \frac{z^2}{\|\mathbf{r}\|^2} - 1 \right) \\ z \left( 5 \frac{z^2}{\|\mathbf{r}\|^2} - 3 \right) \end{bmatrix}$$

where:
- $\mu \approx 3.986004418 \times 10^5 \text{ km}^3/\text{s}^2$ (standard gravitational parameter)
- $R_E \approx 6378.137 \text{ km}$ (Earth equatorial radius)
- $J_2 \approx 1.08262668 \times 10^{-3}$ (second zonal harmonic coefficient)

### Atmospheric Drag Acceleration
The drag acceleration $\mathbf{a}_d$ in $\text{km}/\text{s}^2$ acts opposite to the velocity of the satellite relative to the co-rotating atmosphere $\mathbf{v}_{rel}$:

$$\mathbf{a}_d = -0.5 \cdot C_d \cdot \left(\frac{A}{m}\right) \cdot \rho \cdot 1000.0 \cdot \|\mathbf{v}_{rel}\| \mathbf{v}_{rel}$$

where:
- $C_d$ is the dimensionless drag coefficient.
- $A/m$ is the area-to-mass ratio in $\text{m}^2/\text{kg}$.
- $\rho$ is the atmospheric density in $\text{kg}/\text{m}^3$ (derived from NRLMSISE-00).
- $\mathbf{v}_{rel} = \mathbf{v} - \boldsymbol{\omega}_e \times \mathbf{r} = [v_x + \omega_e y, v_y - \omega_e x, v_z]^T$ (co-rotating atmosphere).
- $1000.0$ is the conversion constant to ECI unit systems.

### Runge-Kutta 4th Order Algorithm
Let $\mathbf{y} = [\mathbf{r}, \mathbf{v}]^T$ be the state vector and $f(t, \mathbf{y}) = [\mathbf{v}, \mathbf{a}_{total}]^T$ be the derivative function. Given a step size $h$, the state is updated as:

$$\mathbf{k}_1 = f(t_n, \mathbf{y}_n)$$
$$\mathbf{k}_2 = f\left(t_n + \frac{h}{2}, \mathbf{y}_n + \frac{h}{2} \mathbf{k}_1\right)$$
$$\mathbf{k}_3 = f\left(t_n + \frac{h}{2}, \mathbf{y}_n + \frac{h}{2} \mathbf{k}_2\right)$$
$$\mathbf{k}_4 = f(t_n + h, \mathbf{y}_n + h \mathbf{k}_3)$$
$$\mathbf{y}_{n+1} = \mathbf{y}_n + \frac{h}{6} (\mathbf{k}_1 + 2\mathbf{k}_2 + 2\mathbf{k}_3 + \mathbf{k}_4)$$

This explicit 4th-order method provides local truncation error on the order of $\mathcal{O}(h^5)$, yielding stable orbital decay trajectories for small step sizes (e.g., $h = 1.0\text{ s}$).
