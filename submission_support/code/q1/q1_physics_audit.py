"""Q1 浓度基准与潜热条件对照；不是新的正式答案。"""
from pathlib import Path
import json
import argparse

import numpy as np
from scipy.integrate import solve_ivp, quad
from scipy.optimize import brentq
from scipy.sparse import lil_matrix

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'common'))

from data_io import ROOT, input_rows, verify_inputs, write_json

P = 101325.  # Explicit scenario pressure, not given in the problem.
RV, RD = 461.52, 287.055
R, LENGTH, RHO, CP, K, H, KM = .02, .25, 820., 2600., .36, 25., 8e-7
RHOD, LV = RHO/3.55, 2.4e6  # Initial wet bulk density interpretation; constant latent heat scenario.
TIMES = np.unique(np.r_[1., 10., np.arange(60., 1801., 60.), 100.])


def saturation_pressure(t_K):
    """ASHRAE liquid-water expression (273.16–473.15 K), as documented by PsychroLib.

    No extrapolation below freezing in the vapor-boundary scenarios.
    """
    t = np.asarray(t_K)
    if np.any((t < 273.16) | (t > 473.15)):
        raise ValueError('饱和水蒸气压公式超出液水适用范围')
    return np.exp(-5.8002206e3/t + 1.3914993 - 4.8640239e-2*t
                  + 4.1764768e-5*t*t - 1.4452093e-8*t*t*t + 6.5459673*np.log(t))


def vapor_pressure(w, pressure=P):
    return pressure*np.asarray(w)/(.621945+np.asarray(w))


def gas_flux(ts, ta, w, activity, coefficient):
    # Dry air mass and dry solid mass are distinct reference quantities.
    pv_inf = vapor_pressure(w)
    # Convert the pressure difference at a common film temperature: sign follows chemical drive.
    film = (ts+ta)/2
    return coefficient*(activity*saturation_pressure(ts)-pv_inf)/(RV*film)


def solve_case(n, mode, activity=1., rtol=1e-9, max_step=10., coefficient='given'):
    """Node FV, actual center/surface unknowns, direct D(C) face flux, Radau.

    mode: baseline; direct_latent (same solid-normalized mass boundary);
    gas_latent (KM reinterpreted as gas-side vapor density coefficient).
    Constant activity is a scenario, not an identified sorption isotherm.
    """
    if mode not in ('baseline', 'direct_latent', 'gas_latent') or not 0 < activity <= 1 or coefficient not in ('given','lewis'):
        raise ValueError('非法物理对照配置')
    room = np.array([[row[j] for j in (1, 2, 3)] for row in input_rows('附件1.xlsx')])
    x = np.linspace(0., R, n+1)
    edges = np.r_[0., (x[:-1]+x[1:])/2, R]
    weights = np.diff(edges**2)/2
    dr, m = R/n, n+1

    def boundary(t, y):
        ta = np.interp(t, room[:, 0], room[:, 1])+273.15
        w = np.interp(t, room[:, 0], room[:, 2])
        ts, cs = y[m-1], y[2*m-1]
        rho_da = (P-vapor_pressure(w))/(RD*ta)
        beta = KM if coefficient == 'given' else H/(rho_da*(1006.+1860.*w))
        mass = RHOD*KM*(cs-w) if mode != 'gas_latent' else gas_flux(ts, ta, w, activity, beta)
        conv = H*(ta-ts)
        latent = 0. if mode == 'baseline' else LV*mass
        return float(mass), float(conv), float(latent)

    def rhs(t, y):
        temp, c = y[:m], y[m:2*m]
        if np.any(c <= 0):
            raise ValueError('物理对照产生非正浓度')
        heat, water = np.zeros(m+1), np.zeros(m+1)
        heat[1:-1] = -K*np.diff(temp)/dr
        water[1:-1] = -7e-9*np.exp(-.89/((c[:-1]+c[1:])/2))*np.diff(c)/dr
        mass, conv, latent = boundary(t, y)
        heat[-1], water[-1] = latent-conv, mass/RHOD
        return np.r_[-np.diff(edges*heat)/(weights*RHO*CP),
                     -np.diff(edges*water)/weights]

    pattern = lil_matrix((2*m, 2*m))
    for i in range(m):
        for j in range(max(0, i-1), min(m, i+2)):
            pattern[i, j] = 1
            pattern[m+i, m+j] = 1
    pattern[m-1, 2*m-1] = pattern[2*m-1, m-1] = 1
    initial = np.r_[np.full(m, 301.15), np.full(m, 2.55)]
    states = np.empty((len(TIMES), 2*m))
    total = np.zeros(3)
    min_temperature, min_moisture = 301.15, 2.55
    for left in np.arange(0., 1800., 60.):
        s = solve_ivp(rhs, (left, left+60.), initial, method='Radau', rtol=rtol,
                      atol=rtol*.01, max_step=max_step, first_step=1e-4,
                      jac_sparsity=pattern.tocsr(), dense_output=True)
        if not s.success:
            raise RuntimeError(s.message)
        select = (TIMES > left) & (TIMES <= left+60.)
        states[select] = s.sol(TIMES[select]).T
        for j in range(3):
            total[j] += quad(lambda t: boundary(t, s.sol(t))[j], left, left+60.,
                             epsabs=1e-8, epsrel=1e-8)[0]*2*np.pi*R*LENGTH
        min_temperature = min(min_temperature, float(s.y[:m].min()))
        min_moisture = min(min_moisture, float(s.y[m:].min()))
        initial = s.y[:, -1]
    vol = np.pi*R*R*LENGTH
    mean_t = states[:, :m]@(2*weights/R**2)
    mean_c = states[:, m:]@(2*weights/R**2)
    sensible = RHO*CP*vol*(mean_t[-1]-301.15)
    mass_lost = RHOD*vol*(2.55-mean_c[-1])
    energy_res = sensible+total[2]-total[1]
    mass_res = mass_lost-total[0]
    surface = np.array([boundary(t, y) for t, y in zip(TIMES, states)])
    pv = vapor_pressure(np.interp(TIMES, room[:,0], room[:,2]))
    dew = np.array([brentq(lambda temp: saturation_pressure(temp)-v, 273.16, 350.) for v in pv])
    final = dict(center_T_C=float(states[-1,0]-273.15), surface_T_C=float(states[-1,m-1]-273.15),
                 center_C=float(states[-1,m]), surface_C=float(states[-1,2*m-1]),
                 mean_C=float(mean_c[-1]), mean_T_C=float(mean_t[-1]-273.15),
                 mass_lost_g=float(mass_lost*1000), sensible_J=float(sensible),
                 convection_J=float(total[1]), latent_J=float(total[2]))
    checks = dict(mass_balance_abs_kg=float(abs(mass_res)), energy_balance_abs_J=float(abs(energy_res)),
                  energy_relative_residual=float(abs(energy_res)/max(1.,abs(total[1]),abs(total[2]))),
                  min_accepted_T_C=min_temperature-273.15, min_accepted_C=min_moisture,
                  evaporating_samples_below_dewpoint=int(np.count_nonzero(
                      (surface[:,0] > 0) & (states[:,m-1] < dew-1e-8))))
    if checks['mass_balance_abs_kg'] > 1e-8 or checks['energy_relative_residual'] > 2e-6:
        raise RuntimeError(f'对照模型收支失败：{checks}')
    if mode == 'gas_latent' and checks['evaporating_samples_below_dewpoint']:
        raise RuntimeError('气相通量方向与露点条件不一致')
    fields = np.c_[states[:,0]-273.15, states[:,m-1]-273.15,
                   states[:,m], states[:,2*m-1], mean_c, surface, dew-273.15]
    return dict(mode=mode, activity=activity, coefficient=coefficient, n=n, rtol=rtol, max_step=max_step,
                final=final, checks=checks), fields


def run(output_dir):
    if output_dir.resolve().is_relative_to((ROOT/'problemA').resolve()):
        raise ValueError('禁止覆盖原始资料')
    inputs = verify_inputs()
    output_dir.mkdir(parents=True, exist_ok=True)
    cases, arrays = {}, {}
    configurations = [('baseline','baseline',1.,'given'), ('direct_latent','direct_latent',1.,'given'),
                      ('gas_aw1','gas_latent',1.,'given'), ('gas_aw08','gas_latent',.8,'given'),
                      ('lewis_aw1','gas_latent',1.,'lewis'), ('lewis_aw08','gas_latent',.8,'lewis')]
    for label, mode, aw, coefficient in configurations:
        coarse, fc = solve_case(400, mode, aw, coefficient=coefficient)
        fine, ff = solve_case(800, mode, aw, coefficient=coefficient)
        tight, ft = solve_case(800, mode, aw, rtol=2e-10, max_step=5., coefficient=coefficient)
        fine['refinement'] = dict(max_T_change_K=float(abs(ff[:,:2]-fc[:,:2]).max()),
                                  max_C_change=float(abs(ff[:,2:5]-fc[:,2:5]).max()),
                                  time_T_change_K=float(abs(ff[:,:2]-ft[:,:2]).max()),
                                  time_C_change=float(abs(ff[:,2:5]-ft[:,2:5]).max()))
        v = fine['refinement']
        if v['max_T_change_K'] > .005 or v['max_C_change'] > .002 or v['time_T_change_K'] > 1e-4 or v['time_C_change'] > 1e-6:
            raise RuntimeError(f'量级对照精度不达标：{label}: {v}')
        cases[label] = fine
        arrays[label] = ff
        arrays[label+'_coarse'] = fc
        arrays[label+'_tight'] = ft
        print(label, json.dumps(fine,ensure_ascii=False), flush=True)
    with np.load(ROOT/'results/q1/fields.npz') as stored:
        baseline_difference = dict(surface_T_K=float(abs(arrays['baseline'][:,1]-stored['temperature_C'][TIMES.astype(int)-1,-1]).max()),
                                   surface_C=float(abs(arrays['baseline'][:,3]-stored['moisture'][TIMES.astype(int)-1,-1]).max()))
    room = np.array([[row[j] for j in (1,2,3)] for row in input_rows('附件1.xlsx')])
    pv = vapor_pressure(room[:,2])
    rh = pv/saturation_pressure(room[:,1]+273.15)
    summary = dict(scope='Q1 physical assumption audit; scenarios, not identified replacement answers',
                   assumptions=dict(pressure_Pa=P, vapor_gas_constant=RV, dry_air_gas_constant=RD,
                     dry_skeleton_density=RHOD, density_interpretation='820 is initial wet bulk density',
                     latent_heat_J_kg=LV, latent_heat_status='assumed constant scale, not given by problem',
                     gas_transfer_coefficient_m_s=KM, activity_scenarios=[1.,.8],
                     lewis_coefficient='H / [rho_da * (1006 + 1860 W)]; assumes Lewis number one, not given',
                     activity_status='fixed hypothetical activities, not measured or fitted'),
                   room_audit=dict(relative_humidity_min=float(rh.min()),relative_humidity_max=float(rh.max()),
                     relative_humidity_initial=float(rh[0]),relative_humidity_1800=float(rh[30]),
                     dewpoint_1800_C=float(brentq(lambda t:saturation_pressure(t)-pv[30],273.16,350)-273.15)),
                   baseline_difference=baseline_difference, cases=cases,
                   input_sha256={p['path']:p['sha256'] for p in inputs})
    write_json(output_dir/'summary.json',summary)
    np.savez_compressed(output_dir/'histories.npz', times_s=TIMES,
        columns=['center_T_C','surface_T_C','center_C','surface_C','mean_C','mass_flux_kg_m2_s',
                 'convective_heat_W_m2','latent_heat_W_m2','dewpoint_C'], **arrays)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'results/q1/physics')
    run(parser.parse_args().output_dir)
