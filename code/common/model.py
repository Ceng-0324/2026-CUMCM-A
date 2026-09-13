"""A 题共用径向求解器及连续场接口。

物理边界：一维径向、均匀材料收缩、有效表面平衡浓度、无显式潜热。
probe_a 保留历史最大单元事件；连续域达标事件留给 Q3 阶段实现。
"""
from __future__ import annotations

from dataclasses import dataclass
import time
import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicHermiteSpline, PchipInterpolator
from scipy.optimize import brentq
from scipy.sparse import lil_matrix
from scipy.special import expi, j0, j1

from data_io import input_rows


def radial_geometry(n):
    edges = np.linspace(0, 1, n + 1)
    centers = (edges[:-1] + edges[1:]) / 2
    weights = np.diff(edges ** 2) / 2
    return edges, centers, weights


def divergence(flux, radius, edges, weights):
    return -np.diff(edges * flux) / (radius * weights)


def sparsity(n):
    pattern = lil_matrix((2*n+1, 2*n+1))
    for i in range(n):
        for j in range(max(0, i-1), min(n, i+2)):
            pattern[i, j] = pattern[i, n+j] = 1
            pattern[n+i, j] = pattern[n+i, n+j] = 1
    pattern[-1, n-1] = pattern[-1, 2*n-1] = 1
    return pattern.tocsr()


def material_parameters(c, t, appendix):
    if appendix not in (2, 3, 4):
        raise ValueError("物性附录必须为 2、3 或 4")
    if appendix == 2:
        return 820 + 0*c, 2600 + 0*c, .36 + 0*c, 7e-9 + 0*c, .89
    if appendix == 3:
        return 650+128*c, 1450+2736*c/(c+1), .21+.38*c/(c+1), 2.4e-3*np.exp(-3850/t), .45
    return 760+90*c, 1850+2150*c/(c+1), .12+.20*c/(c+1), 4.2e-4*np.exp(-3850/t), .30


def kirchhoff(c, a):
    # Integral of exp(-a/C); this retains the nonlinear surface resistance.
    safe = np.maximum(c, 1e-12)
    return safe*np.exp(-a/safe) + a*expi(-a/safe)


def inverse_kirchhoff(value, a, upper):
    """单调积分的向量二分反解，不裁剪插值产生的非法浓度。"""
    value = np.asarray(value, dtype=float)
    if np.any(~np.isfinite(value)) or np.any(value < 0):
        raise ValueError('Kirchhoff 场必须为有限非负值')
    lo = np.zeros_like(value)
    hi = np.full_like(value, float(upper))
    if np.any(value > kirchhoff(hi, a) + 1e-13):
        raise ValueError('Kirchhoff 反解上界不足')
    for _ in range(46):
        mid = (lo+hi)/2
        below = kirchhoff(mid, a) < value
        lo = np.where(below, mid, lo)
        hi = np.where(below, hi, mid)
    return (lo+hi)/2


def reconstruct_profile(centers, values, surface_value, surface_gradient):
    """中点近似量的连续重构，坐标为 ξ；中心用偶二次外推。

    内点斜率取 PCHIP，端点斜率取中心对称和 Robin 通量。
    这些自由度沿用原型的单元中点解释，不视作精确体积平均值。
    """
    center = (9*values[0]-values[1])/8
    nodes = np.r_[0., centers, 1.]
    augmented = np.r_[center, values, surface_value]
    slopes = PchipInterpolator(nodes, augmented).derivative()(nodes)
    slopes[0], slopes[-1] = 0., surface_gradient
    return CubicHermiteSpline(nodes, augmented, slopes, extrapolate=False)


class RadialModel:
    km, h, r0 = 8e-7, 25., .02

    def __init__(self, n, appendix=3, shrink=False, boundary='mean'):
        if not isinstance(n, (int, np.integer)) or n < 4:
            raise ValueError('网格数必须为不小于 4 的整数')
        if appendix not in (2, 3, 4) or boundary not in ('mean', 'last'):
            raise ValueError('物性附录或边界延拓配置非法')
        self.n, self.appendix, self.shrink = n, appendix, shrink
        self.room = np.array([[row[j] for j in (1, 2, 3)] for row in input_rows('附件1.xlsx')])
        self.radii = np.array([[row[j] for j in (1, 2)] for row in input_rows('附件2.xlsx')])
        self.tail = self.room[self.room[:, 0] >= 10800, 1:].mean(axis=0)
        if boundary == 'last':
            self.tail = self.room[-1, 1:]
        self.edges, self.centers, self.weights = radial_geometry(n)
        self.moisture_floor_evaluations = 0

    def environment(self, t):
        if t <= self.room[-1, 0]:
            return (np.interp(t, self.room[:, 0], self.room[:, 1])+273.15,
                    np.interp(t, self.room[:, 0], self.room[:, 2]))
        return self.tail[0]+273.15, self.tail[1]

    def radius(self, t):
        return np.interp(t, self.radii[:, 0], self.radii[:, 1])*.01 if self.shrink else self.r0

    def fluxes(self, t, y):
        n, km, h = self.n, self.km, self.h
        temp, moisture = y[:n], y[n:2*n]
        self.moisture_floor_evaluations += int(np.any(moisture < 1e-10))
        c = np.maximum(moisture,1e-10)
        rad = self.radius(t)
        dr = rad/n
        ta, ca = self.environment(t)
        rho, cp, k, base, a = material_parameters(c,temp,self.appendix)
        heat = np.zeros(n+1)
        kface = 2*k[:-1]*k[1:]/(k[:-1]+k[1:])
        heat[1:-1] = -kface*np.diff(temp)/dr
        heat[-1] = (temp[-1]-ta)/(.5*dr/k[-1]+1/h)
        water = np.zeros(n+1)
        baseface = (base[:-1]+base[1:])/2
        water[1:-1] = -baseface*np.diff(kirchhoff(c,a))/dr
        pcell = kirchhoff(c[-1],a)

        def surface_equation(cs):
            return base[-1]*(pcell-kirchhoff(cs,a))-.5*dr*km*(cs-ca)

        cs = brentq(surface_equation,min(c[-1],ca),max(c[-1],ca),xtol=1e-12)
        water[-1] = km*(cs-ca)
        ts = ta+heat[-1]/h
        return heat, water, ts, cs, rho, cp, k, base, a

    def rhs(self, t, y):
        rad = self.radius(t)
        heat, water, _, _, rho, cp, *_ = self.fluxes(t, y)
        ct = divergence(water,rad,self.edges,self.weights)
        tt = divergence(heat,rad,self.edges,self.weights)/(rho*cp)
        lost_rate = 2*water[-1]/rad
        return np.concatenate([tt,ct,[lost_rate]])


@dataclass
class FieldSamples:
    time_s: np.ndarray
    radius_m: np.ndarray
    temperature_K: np.ndarray
    moisture: np.ndarray
    temperature_gradient_K_m: np.ndarray
    moisture_gradient_per_m: np.ndarray


class RadialSolution:
    """公共采样返回 (时间数, 位置数) 数组，显式处理越界和 t=0 初值。"""

    def __init__(self, model, segments, configuration):
        self.model, self.segments, self.configuration = model, segments, configuration
        self.ends = np.array([s.t[-1] for s in segments])
        self.end_s = float(self.ends[-1])
        self.t = np.concatenate([s.t if i == 0 else s.t[1:] for i, s in enumerate(segments)])
        self.y = np.concatenate([s.y if i == 0 else s.y[:, 1:] for i, s in enumerate(segments)], axis=1)

    def state(self, times_s):
        times = np.atleast_1d(np.asarray(times_s, dtype=float))
        if times.ndim != 1 or not len(times) or np.any(~np.isfinite(times)):
            raise ValueError('采样时间必须为非空、有限的一维数组')
        if np.any(times < 0) or np.any(times > self.end_s):
            raise ValueError('采样时间超出实际积分区间')
        groups = np.searchsorted(self.ends, times, side='left')
        result = np.empty((2*self.model.n+1, len(times)))
        for i in np.unique(groups):
            use = groups == i
            result[:, use] = self.segments[i].sol(times[use])
        return result

    def sample(self, times_s, positions, *, coordinate='radius', outside='raise'):
        times = np.atleast_1d(np.asarray(times_s, dtype=float))
        positions = np.atleast_1d(np.asarray(positions, dtype=float))
        if positions.ndim != 1 or not len(positions) or np.any(~np.isfinite(positions)):
            raise ValueError('采样位置必须为非空、有限的一维数组')
        if coordinate not in ('radius', 'material') or outside not in ('raise', 'nan'):
            raise ValueError('coordinate 或 outside 配置非法')
        states = self.state(times)
        model, n = self.model, self.model.n
        radii = np.array([model.radius(t) for t in times])
        xi = (np.broadcast_to(positions, (len(times), len(positions))).copy()
              if coordinate == 'material' else positions[None, :]/radii[:, None])
        invalid = (xi < 0) | (xi > 1)
        if outside == 'raise' and np.any(invalid):
            raise ValueError('采样位置超出当时药材范围')
        fields = [np.full(xi.shape, np.nan) for _ in range(4)]
        for i, t in enumerate(times):
            valid = ~invalid[i]
            if not np.any(valid):
                continue
            if t == 0:
                for field, value in zip(fields, [301.15, 2.55, 0., 0.]):
                    field[i, valid] = value
                continue
            y, rad, x = states[:, i], radii[i], xi[i, valid]
            heat, water, ts, cs, _, _, k, base, a = model.fluxes(t, y)
            pt = reconstruct_profile(model.centers, y[:n], ts, -rad*heat[-1]/k[-1])
            pk = reconstruct_profile(model.centers, kirchhoff(y[n:2*n], a),
                                     kirchhoff(cs, a), -rad*water[-1]/base[-1])
            c = inverse_kirchhoff(pk(x), a, 2*max(2.55, float(y[n:2*n].max()), cs))
            fields[0][i, valid], fields[1][i, valid] = pt(x), c
            fields[2][i, valid] = pt(x, 1)/rad
            fields[3][i, valid] = pk(x, 1)/(rad*np.exp(-a/c))
        return FieldSamples(times, xi*radii[:, None], *fields)


def solve_radial(n, *, appendix=3, shrink=False, boundary='mean', duration_s=1800.,
                 rtol=2e-6, atol=None, max_step=600., align_environment=False,
                 stop_at_cell_threshold=False, method='BDF'):
    if method not in ('BDF', 'Radau'):
        raise ValueError('时间积分方法必须为 BDF 或 Radau')
    if any(not np.isfinite(x) or x <= 0 for x in [duration_s, rtol, max_step]):
        raise ValueError('容差、步长及积分时长必须为有限正数')
    if atol is not None and (np.any(~np.isfinite(atol)) or np.any(np.asarray(atol) <= 0)):
        raise ValueError('绝对容差必须为有限正数')
    model = RadialModel(n, appendix, shrink, boundary)
    def threshold(t,y):
        return np.max(y[n:2*n])-.15
    threshold.terminal = True
    threshold.direction = -1
    initial = np.concatenate([np.full(n,301.15),np.full(n,2.55),[0.]])
    stops = np.array([0., duration_s])
    if align_environment:
        knots = model.room[:, 0]
        if shrink:
            knots = np.r_[knots, model.radii[:, 0]]
        stops = np.unique(np.r_[0., knots[(knots > 0) & (knots < duration_s)], duration_s])
    segments = []
    for left, right in zip(stops, stops[1:]):
        sol = solve_ivp(model.rhs, (left, right), initial, method=method, rtol=rtol,
                        atol=rtol*.01 if atol is None else atol,
                        events=threshold if stop_at_cell_threshold else None,
                        max_step=max_step, dense_output=True, jac_sparsity=sparsity(n))
        if not sol.success:
            raise RuntimeError(sol.message)
        segments.append(sol)
        initial = sol.y[:, -1]
        if sol.status == 1:
            break
    config = dict(n=n, appendix=appendix, shrink=shrink, boundary=boundary,
                  duration_s=duration_s, rtol=rtol, atol=atol, max_step=max_step,
                  align_environment=align_environment,
                  stop_at_cell_threshold=stop_at_cell_threshold, method=method)
    return RadialSolution(model, segments, config)


def probe_a(n, appendix=3, shrink=False, boundary="mean", rtol=2e-6,
            max_step=600, max_hours=168):
    """历史可行性实验保留最大单元事件和单元采样口径。"""
    start = time.perf_counter()
    solution = solve_radial(n, appendix=appendix, shrink=shrink, boundary=boundary,
                            rtol=rtol, max_step=max_step, duration_s=max_hours*3600,
                            stop_at_cell_threshold=True)
    sol, weights = solution.segments[0], solution.model.weights
    c = sol.y[n:2*n]
    balance = 2*weights @ c + sol.y[-1]-2.55
    event = float(sol.t_events[0][0]) if len(sol.t_events[0]) else None
    samples = {}
    for hours in [.5,3,24,48,72]:
        if hours*3600 <= sol.t[-1]:
            state = sol.sol(hours*3600)
            samples[str(hours)] = {"max_C":float(max(state[n:2*n])),
                                    "min_C":float(min(state[n:2*n])),
                                    "center_T_C":float(state[0]-273.15)}
    if np.min(c) <= 0 or np.max(abs(balance)) >= 2e-6:
        raise RuntimeError("水分正性或归一化质量平衡验证失败")
    return {
        "n":n,"appendix":appendix,"shrink":shrink,"boundary_extension":boundary,
        "rtol":rtol,"max_step_s":max_step,"success":sol.success,
        "drying_event_hours":event/3600 if event is not None else None,
        "radius_extrapolated_after_72h":bool(shrink and sol.t[-1]>259200),
        "event_uses_max_cell_C_not_certified_continuous_max":True,
        "min_C":float(c.min()),"max_C":float(c.max()),
        "final_center_cell_C":float(c[0,-1]),
        "max_dry_mass_normalized_balance_residual":float(np.max(abs(balance))),
        "rhs_evaluations":sol.nfev,"elapsed_s":time.perf_counter()-start,
        "samples":samples,
    }


def analytic_radial_check(n):
    edges, centers, weights = radial_geometry(n)
    radius, diff, km = .02, 1e-8, 8e-7
    dr = radius/n
    bi = km*radius/diff
    mu = brentq(lambda x:x*j1(x)-bi*j0(x),1e-8,2.4048)

    def rhs(t,c):
        f = np.zeros(n+1)
        f[1:-1] = -diff*np.diff(c)/dr
        f[-1] = c[-1]/(.5*dr/diff+1/km)
        return divergence(f,radius,edges,weights)

    end = 15000
    sol = solve_ivp(rhs,(0,end),j0(mu*centers),method="BDF",rtol=1e-9,atol=1e-11)
    exact = j0(mu*centers)*np.exp(-diff*mu**2*end/radius**2)
    if not sol.success:
        raise RuntimeError(sol.message)
    return {"n":n,"max_error":float(np.max(abs(sol.y[:,-1]-exact))),
            "type":"constant diffusion cylinder Robin eigenmode"}
