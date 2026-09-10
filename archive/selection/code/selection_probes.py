"""Bounded feasibility probes, not official solutions or submission workbooks.

uv run --no-project --cache-dir /private/tmp/cumcm-uv-cache \
  --with scipy==1.17.1 python code/selection_probes.py --part a
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import time

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, linprog
from scipy.sparse import lil_matrix
from scipy.special import expi, j0, j1

from selection_audit import ROOT, matrix, read_xlsx

OUT = ROOT / "results/selection"


def write_result(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                      allow_nan=False) + "\n", encoding="utf-8")


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
    room_rows = read_xlsx(ROOT / "problemA/附件/附件1.xlsx")["Sheet1"]["rows"]
    room = np.array([list(row.values()) for i,row in room_rows.items() if i>1])
    radius_rows = read_xlsx(ROOT / "problemA/附件/附件2.xlsx")["Sheet1"]["rows"]
    radii = np.array([list(row.values()) for i,row in radius_rows.items() if i>1])
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
    assert np.min(c) > 0
    assert np.max(abs(balance)) < 2e-6
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
    assert sol.success
    return {"n":n,"max_error":float(np.max(abs(sol.y[:,-1]-exact))),
            "type":"constant diffusion cylinder Robin eigenmode"}


def dispatch(net, price, e0=6000, terminal=6000):
    n = len(net)
    dt, eta, limit = 1/6,.9,5000
    # Columns: grid, charge, discharge, spill, SOC[0..n].
    size = 5*n+1
    obj = np.zeros(size)
    obj[:n] = price*dt
    aeq = lil_matrix((2*n+2,size))
    b = np.zeros(2*n+2)
    for i in range(n):
        aeq[i,i]=1
        aeq[i,n+i]=-1
        aeq[i,2*n+i]=1
        aeq[i,3*n+i]=-1
        b[i]=net[i]
        aeq[n+i,4*n+i+1]=1
        aeq[n+i,4*n+i]=-1
        aeq[n+i,n+i]=-eta*dt
        aeq[n+i,2*n+i]=dt/eta
    aeq[-2,4*n]=1
    aeq[-1,5*n]=1
    b[-2:]=[e0,terminal]
    bounds = [(0,None)]*n + [(0,limit)]*(2*n) + [(0,None)]*n + [(1200,10800)]*(n+1)
    result = linprog(obj,A_eq=aeq.tocsr(),b_eq=b,bounds=bounds,method="highs")
    if not result.success:
        raise RuntimeError(result.message)
    grid,charge,discharge,spill=result.x[:4*n].reshape(4,n)
    soc=result.x[4*n:]
    checks={"max_equality_residual":float(max(abs(aeq @ result.x-b))),
            "SOC_min":float(min(soc)),"SOC_max":float(max(soc)),
            "terminal_SOC":float(soc[-1]),
            "simultaneous_charge_discharge_kW":float(max(np.minimum(charge,discharge)))}
    assert checks['max_equality_residual']<1e-6
    assert checks['simultaneous_charge_discharge_kW']<1e-6
    return {"cost":float(result.fun),"grid_kWh":float(sum(grid)*dt),
            "spill_kWh":float(sum(spill)*dt),"checks":checks},grid,charge,discharge


def execute_day(grid,actual_net,planned_discharge,e0):
    dt,eta=1/6,.9
    soc=[e0]
    emergency=[]
    charge=[]
    discharge=[]
    spill=[]
    for i,net in enumerate(actual_net):
        balance=grid[i]-net
        if balance>=0:
            c=min(balance,5000,(10800-soc[-1])/(eta*dt))
            d=0
            u=0
            s=balance-c
        else:
            d=min(-balance,planned_discharge[i],5000,(soc[-1]-1200)*eta/dt)
            c=0
            u=-balance-d
            s=0
        soc.append(soc[-1]+eta*c*dt-d*dt/eta)
        emergency.append(u)
        charge.append(c)
        discharge.append(d)
        spill.append(s)
    c,d,u,s=map(np.asarray,(charge,discharge,emergency,spill))
    residual=grid+d+u-actual_net-c-s
    check={"max_power_residual_kW":float(max(abs(residual))),
           "SOC_min":float(min(soc)),"SOC_max":float(max(soc)),
           "max_charge_kW":float(max(c)),"max_discharge_kW":float(max(d))}
    assert check['max_power_residual_kW']<1e-6
    assert 1200-1e-6<=min(soc)<=max(soc)<=10800+1e-6
    return soc[-1],u,check


def probe_c():
    reference=read_xlsx(ROOT/'C题/附件/附件1.xlsx')['Sheet1']['rows']
    data=np.array([[r[j] for j in [2,3,4]] for i,r in reference.items() if i>1])
    price,load,pv=data.T
    net=load-pv
    started=time.perf_counter()
    q1,_,_,_=dispatch(net,price)
    q1['no_battery_cost']=float(np.dot(price,np.maximum(net,0))/6)
    q1['elapsed_s']=time.perf_counter()-started
    sheets=read_xlsx(ROOT/'C题/附件/附件2.xlsx')
    net=np.asarray(matrix(sheets['小区负载']))-np.asarray(matrix(sheets['光伏发电实际功率']))
    results=[]
    e0=6000
    # Jan 1 is a cold-start execution rule with no advance actual information.
    # Jan 2 onward uses at most the preceding seven days at the same time of day.
    for day in range(38):
        if day==0:
            grid=np.zeros(144)
            planned_d=np.zeros(144)
            plan_cost=0
            training_last=None
        else:
            history=net[max(0,day-7):day]
            predicted=history.mean(axis=0)
            plan,grid,_,planned_d=dispatch(predicted,price,e0=e0)
            plan_cost=plan['cost']
            training_last=(datetime(2025,1,1)+timedelta(days=day-1)).date().isoformat()
        start_e=e0
        e0,u,checks=execute_day(grid,net[day],planned_d,e0)
        date=(datetime(2025,1,1)+timedelta(days=day)).date().isoformat()
        assert training_last is None or training_last<date
        results.append({'date':date,'training_last_date':training_last,
                        'initial_SOC':start_e,'final_SOC':e0,
                        'planned_cost':plan_cost,'emergency_kWh':float(sum(u)/6),
                        'emergency_cost':float(np.dot(price,u)*5/6),'checks':checks})
    feb=results[31:]
    return {'assumptions':{'dt_hours':1/6,'price_load_pv_samples':'right endpoint held over preceding ten minutes',
                           'efficiency_each':.9,'spill':'free, no sale',
                           'Q2_forecast':'previous 1..7 days same-time mean net load',
                           'Q2_terminal_target_kWh':6000,
                           'Q2_execution':'use scheduled discharge cap; absorb realized surplus; emergency fills deficit',
                           'Q2_cold_start':'Jan 1 no advance purchase, observed deficits emergency only',
                           'Q2_scope':'Jan warm-up plus Feb 1..7, no tuning, no Q3/Q4 dispatch'},
            'Q1':q1,'Q2_probe':{'days':results,'February_week_planned_cost':sum(d['planned_cost'] for d in feb),
                                'February_week_emergency_cost':sum(d['emergency_cost'] for d in feb),
                                'February_week_emergency_kWh':sum(d['emergency_kWh'] for d in feb)},
            'scope':'Feasible baseline only, not a competitive or optimal annual policy'}


def probe_a_effects():
    runs = {}
    for name, appendix, shrink in [('base',3,False),('radius_only',3,True),
                                   ('properties_only',4,False),('both',4,True)]:
        runs[name] = probe_a(128,appendix=appendix,shrink=shrink,
                             rtol=2e-7,max_step=300,max_hours=200)
    t00,t10,t01,t11 = [runs[k]['drying_event_hours']
                      for k in ['base','radius_only','properties_only','both']]
    if any(t is None for t in [t00,t10,t01,t11]):
        raise RuntimeError('An ablation case did not reach the threshold')
    effects = {
        'radius_order_averaged_hours':.5*((t10-t00)+(t11-t01)),
        'properties_order_averaged_hours':.5*((t01-t00)+(t11-t10)),
        'interaction_hours':t11-t10-t01+t00,
        'total_change_hours':t11-t00,
    }
    assert abs(effects['radius_order_averaged_hours']
               + effects['properties_order_averaged_hours']
               - effects['total_change_hours']) < 1e-10
    return {'scope':'Conditional mechanism study, not official answers or physical causal identification',
            'assumptions_source':'A_feasibility_probe.json; same probe_a model',
            'property_change':'All rho, cp, k, D formulas change together',
            'radius_only_uses_given_empirical_radius_curve':True,
            'counterfactual_radius_is_prescribed_not_induced_by_simulated_moisture':True,
            'runs':runs,'effects':effects}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--part',choices=['a','c','all','a-effects'],default='a')
    parser.add_argument('--grids',nargs='+',type=int,default=[32,64,128])
    args=parser.parse_args()
    if args.part in ['c','all'] and not (ROOT/'C题/附件/附件1.xlsx').exists():
        parser.error('C 题原始附件当前不在工作区；现有 problemA 目录可运行 --part a 或 --part a-effects。')
    if args.part in ['a','all']:
        results={'assumptions':[
            '1D radial cylinder; no axial/latent heat terms',
            'thermal empirical density only used in heat capacity; not asserted as dry skeleton density',
            'homogeneous contracting dry skeleton, constant material dry-mass weights',
            'bulk Robin mass coefficient assumed inherited for all problems',
            'room concentration used as effective surface-equilibrium concentration',
            'radius linear interpolation; held constant beyond 72h if required',
            'Kirchhoff flux for nonlinear moisture; BDF integration',
            'Only conditional feasibility; no claim of unique official model or four-decimal accuracy'],
                 'analytic_checks':[],'runs':[]}
        for n in args.grids:
            results['analytic_checks'].append(analytic_radial_check(n))
            for appendix,shrink in [(3,False),(4,True)]:
                run=probe_a(n,appendix=appendix,shrink=shrink)
                results['runs'].append(run)
                print(json.dumps(run),flush=True)
                write_result('A_feasibility_probe.json',results)
        finest=max(args.grids)
        for appendix,shrink in [(3,False),(4,True)]:
            run=probe_a(finest,appendix=appendix,shrink=shrink,rtol=2e-7,max_step=300)
            results['runs'].append(run)
            print(json.dumps(run),flush=True)
            run=probe_a(finest,appendix=appendix,shrink=shrink,boundary='last')
            results['runs'].append(run)
            print(json.dumps(run),flush=True)
        write_result('A_feasibility_probe.json',results)
    if args.part in ['c','all']:
        results=probe_c()
        write_result('C_feasibility_probe.json',results)
        print(json.dumps({'Q1':results['Q1'],'Q2_days':len(results['Q2_probe']['days']),
                          'Q2_last':results['Q2_probe']['days'][-1]}),flush=True)
    if args.part == 'a-effects':
        results = probe_a_effects()
        write_result('A_mechanism_probe.json',results)
        print(json.dumps({'hours':{k:v['drying_event_hours'] for k,v in results['runs'].items()},
                          'effects':results['effects']},ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
