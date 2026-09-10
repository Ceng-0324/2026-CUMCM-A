"""A 题可行性原型：模型和数值方法沿用选题试算，不是最终求解器。

已知边界：一维径向、均匀材料收缩、有效表面平衡浓度、无显式潜热。
停止事件使用最大单元浓度；连续中心与表面重构尚待正式实现。
"""
from __future__ import annotations

import time
import numpy as np
from scipy.integrate import solve_ivp
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


def probe_a(n, appendix=3, shrink=False, boundary="mean", rtol=2e-6,
            max_step=600, max_hours=168):
    if n < 4 or rtol <= 0 or max_step <= 0 or max_hours <= 0:
        raise ValueError("网格数至少为 4，容差、步长及积分时长必须为正")
    if boundary not in ("mean", "last"):
        raise ValueError("边界延拓只能为 mean 或 last")
    room = np.array([[row[j] for j in (1, 2, 3)] for row in input_rows("附件1.xlsx")])
    radii = np.array([[row[j] for j in (1, 2)] for row in input_rows("附件2.xlsx")])
    tail = room[room[:,0]>=10800, 1:].mean(axis=0)
    if boundary == "last":
        tail = room[-1, 1:]
    edges, centers, weights = radial_geometry(n)
    km, h, r0 = 8e-7, 25, .02

    def environment(t):
        if t <= room[-1,0]:
            return np.interp(t,room[:,0],room[:,1])+273.15, np.interp(t,room[:,0],room[:,2])
        return tail[0]+273.15, tail[1]

    def radius(t):
        return np.interp(t,radii[:,0],radii[:,1])*.01 if shrink else r0

    def rhs(t,y):
        temp, moisture = y[:n], y[n:2*n]
        c = np.maximum(moisture,1e-10)
        rad = radius(t)
        dr = rad/n
        ta, ca = environment(t)
        rho, cp, k, base, a = material_parameters(c,temp,appendix)
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
        ct = divergence(water,rad,edges,weights)
        tt = divergence(heat,rad,edges,weights)/(rho*cp)
        # For homogeneous radial material contraction, dry mass weights stay fixed.
        lost_rate = 2*water[-1]/rad
        return np.concatenate([tt,ct,[lost_rate]])

    def threshold(t,y):
        return np.max(y[n:2*n])-.15

    threshold.terminal = True
    threshold.direction = -1
    initial = np.concatenate([np.full(n,301.15),np.full(n,2.55),[0.]])
    start = time.perf_counter()
    sol = solve_ivp(rhs,(0,max_hours*3600),initial,method="BDF",rtol=rtol,
                    atol=rtol*.01,events=threshold,max_step=max_step,
                    dense_output=True,jac_sparsity=sparsity(n))
    if not sol.success:
        raise RuntimeError(sol.message)
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
