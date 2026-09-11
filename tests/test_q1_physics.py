"""物理对照验收：湿空气换算、通量方向及质量/能量反馈。"""
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code/q1'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'code/common'))
from q1_physics_audit import saturation_pressure, vapor_pressure, gas_flux, solve_case, P


class PhysicsAuditTests(unittest.TestCase):
    def test_psychrometric_reference_values_and_inverse(self):
        self.assertAlmostEqual(float(saturation_pressure(293.15)), 2338.8037, places=3)
        pressure = np.array([1200., 2338.8037, 5000.])
        w = .621945*pressure/(P-pressure)
        np.testing.assert_allclose(vapor_pressure(w), pressure, rtol=1e-14)
        with self.assertRaises(ValueError):
            saturation_pressure(260.)

    def test_gas_flux_changes_sign_at_surface_equilibrium(self):
        pv = float(saturation_pressure(303.15))
        w = .621945*pv/(P-pv)
        self.assertAlmostEqual(float(gas_flux(303.15, 315., w, 1., .02)), 0., places=14)
        self.assertLess(gas_flux(302.15, 315., w, 1., .02), 0.)
        self.assertGreater(gas_flux(304.15, 315., w, 1., .02), 0.)
        self.assertLess(gas_flux(303.15, 315., w, .8, .02), 0.)

    def test_latent_term_cools_but_does_not_change_uncoupled_mass_equation(self):
        baseline, fb = solve_case(40, 'baseline')
        latent, fl = solve_case(40, 'direct_latent')
        np.testing.assert_allclose(fb[:,2:5], fl[:,2:5], atol=1e-7, rtol=0)
        self.assertLess(latent['final']['surface_T_C'], baseline['final']['surface_T_C']-10)
        self.assertLess(latent['checks']['energy_relative_residual'], 2e-6)
        self.assertGreater(latent['checks']['evaporating_samples_below_dewpoint'], 0)

    def test_vapor_boundary_allows_condensation_without_clipping(self):
        result, fields = solve_case(40, 'gas_latent', .8)
        self.assertLess(result['final']['mass_lost_g'], 0.)
        self.assertGreater(result['final']['mean_C'], 2.55)
        self.assertEqual(result['checks']['evaporating_samples_below_dewpoint'], 0)
        self.assertTrue(np.any(fields[:,5] < 0))


if __name__ == '__main__':
    unittest.main()
