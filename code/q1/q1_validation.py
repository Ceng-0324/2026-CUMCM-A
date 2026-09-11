"""Q1 独立热方程基准、连续场检查及误差指标。"""
import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import j0, j1, jn_zeros


def heat_reference(room, times_s, radius_m, modes=256, axial_modes=0):
    """实际分段线性烘房输入的圆柱 Robin 特征展开；逐段解析推进模态。

    常热物性、无潜热的 Q1 适用；不调用有限体积求解器。
    """
    times = np.asarray(times_s, dtype=float)
    r = np.asarray(radius_m, dtype=float)
    bi, alpha, radius = 25*.02/.36, .36/(820*2600), .02
    upper = jn_zeros(0, modes)
    lower = np.r_[1e-12, jn_zeros(1, modes-1)]
    mu = np.array([brentq(lambda x: x*j1(x)-bi*j0(x), a, b)
                   for a, b in zip(lower, upper)])
    decay = alpha*(mu/radius)**2
    coefficients = 2*j1(mu)/(mu*(j0(mu)**2+j1(mu)**2))
    shapes = j0(mu[:, None]*r[None, :]/radius)
    if axial_modes:
        # Finite cylinder with both ends exchanging heat, evaluated at z=0.
        half_length, axial_bi = .125, 25*.125/.36
        nu = np.array([brentq(lambda x: x*np.tan(x)-axial_bi,
                             i*np.pi+1e-9, (i+.5)*np.pi-1e-9)
                       for i in range(axial_modes)])
        axial_coeff = 4*np.sin(nu)/(2*nu+np.sin(2*nu))
        decay = (decay[:, None]+alpha*(nu[None, :]/half_length)**2).ravel()
        coefficients = (coefficients[:, None]*axial_coeff[None, :]).ravel()
        shapes = np.repeat(shapes, axial_modes, axis=0)
    amplitudes = np.zeros(len(decay))
    output = np.empty((len(times), len(r)))
    current, segment = 0., 0
    for i in np.argsort(times):
        target = times[i]
        while current < target:
            while segment+1 < len(room)-1 and current >= room[segment+1, 0]:
                segment += 1
            end = min(target, room[segment+1, 0])
            if end <= current:
                raise ValueError('独立热基准不对附件时间范围外作延拓')
            slope = ((room[segment+1, 1]-room[segment, 1]) /
                     (room[segment+1, 0]-room[segment, 0]))
            dt = end-current
            amplitudes = (amplitudes*np.exp(-decay*dt)
                          + coefficients*slope*np.expm1(-decay*dt)/decay)
            current = end
        output[i] = np.interp(target, room[:, 0], room[:, 1])+amplitudes @ shapes
    return output


def difference(coarse, fine):
    return {
        'max_temperature_difference_K': float(np.max(abs(coarse.temperature_K-fine.temperature_K))),
        'max_moisture_difference': float(np.max(abs(coarse.moisture-fine.moisture))),
    }


def diagnose(solution, samples):
    model, n = solution.model, solution.model.n
    m = solution.y[n:2*n]
    balance = 2*model.weights @ m+solution.y[-1]-2.55
    surface = solution.sample(samples.time_s, [0., 1.], coordinate='material')
    rooms = np.array([model.environment(t) for t in samples.time_s])
    ts, cs = surface.temperature_K[:, -1], surface.moisture[:, -1]
    hres = -.36*surface.temperature_gradient_K_m[:, -1]-model.h*(ts-rooms[:, 0])
    d = 7e-9*np.exp(-.89/cs)
    cres = -d*surface.moisture_gradient_per_m[:, -1]-model.km*(cs-rooms[:, 1])
    energy_out, water_out = 0., 0.
    # Independent quadrature of the time-continuous boundary flux over each input interval.
    for segment in solution.segments:
        left, right = segment.t[0], segment.t[-1]
        energy_out += quad(lambda t: 2*model.fluxes(t, segment.sol(t))[0][-1]/model.r0,
                           left, right, epsabs=1e-3, epsrel=1e-8)[0]
        water_out += quad(lambda t: 2*model.fluxes(t, segment.sol(t))[1][-1]/model.r0,
                          left, right, epsabs=1e-10, epsrel=1e-8)[0]
    thermal_change = 820*2600*(2*model.weights @ solution.y[:n, -1]-301.15)
    water_change = 2*model.weights @ solution.y[n:2*n, -1]-2.55
    residual_T = thermal_change+energy_out
    result = {
        'min_accepted_cell_moisture': float(m.min()),
        'max_accepted_cell_moisture': float(m.max()),
        'min_sample_moisture': float(np.min(samples.moisture)),
        'max_sample_moisture': float(np.max(samples.moisture)),
        'min_sample_temperature_C': float(np.min(samples.temperature_K)-273.15),
        'max_sample_temperature_C': float(np.max(samples.temperature_K)-273.15),
        'max_discrete_water_balance_residual': float(np.max(abs(balance))),
        'independent_water_balance_residual': float(abs(water_change+water_out)),
        'independent_energy_balance_relative_residual': float(abs(residual_T)/max(1., abs(thermal_change))),
        'max_surface_heat_Robin_residual_W_m2': float(np.max(abs(hres))),
        'max_surface_moisture_Robin_residual_m_s': float(np.max(abs(cres))),
        'max_center_temperature_gradient_K_m': float(np.max(abs(surface.temperature_gradient_K_m[:, 0]))),
        'max_center_moisture_gradient_per_m': float(np.max(abs(surface.moisture_gradient_per_m[:, 0]))),
        'max_outward_moisture_increase': float(max(0., np.max(np.diff(samples.moisture, axis=1)))),
        'moisture_floor_evaluations': model.moisture_floor_evaluations,
        'input_intervals': len(solution.segments),
        'accepted_steps': len(solution.t)-1,
        'rhs_evaluations': sum(s.nfev for s in solution.segments),
    }
    if result['min_sample_moisture'] <= 0 or result['max_sample_moisture'] > 2.55+1e-7:
        raise RuntimeError('重构浓度违反正性或初值上界')
    for key, limit in [('max_discrete_water_balance_residual', 1e-8),
                       ('independent_water_balance_residual', 1e-6),
                       ('independent_energy_balance_relative_residual', 1e-6),
                       ('max_surface_heat_Robin_residual_W_m2', 1e-7),
                       ('max_surface_moisture_Robin_residual_m_s', 1e-12),
                       ('max_outward_moisture_increase', 1e-7),
                       ('moisture_floor_evaluations', 0)]:
        if result[key] > limit:
            raise RuntimeError(f'Q1 验证失败：{key}={result[key]} > {limit}')
    return result
