"""中心、表面、时空采样及独立温度基准的物理接口测试。"""
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code/common'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code/q1'))
from model import inverse_kirchhoff, kirchhoff, solve_radial
from q1_validation import heat_reference


class SamplingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solution = solve_radial(64, appendix=2, duration_s=120, rtol=1e-10,
                                   atol=1e-11, max_step=5, align_environment=True)

    def test_initial_field_is_uniform_including_boundary(self):
        field = self.solution.sample([0], np.linspace(0, .02, 17))
        np.testing.assert_allclose(field.temperature_K, 301.15, atol=1e-12)
        np.testing.assert_allclose(field.moisture, 2.55, atol=1e-12)
        self.assertEqual(field.temperature_K.shape, (1, 17))

    def test_center_and_surface_gradients_obey_boundaries(self):
        field = self.solution.sample([1., 60., 120.], [0., .02])
        np.testing.assert_allclose(field.temperature_gradient_K_m[:, 0], 0., atol=1e-12)
        np.testing.assert_allclose(field.moisture_gradient_per_m[:, 0], 0., atol=1e-12)
        room = np.array([self.solution.model.environment(t) for t in field.time_s])
        np.testing.assert_allclose(-.36*field.temperature_gradient_K_m[:, -1],
                                   25*(field.temperature_K[:, -1]-room[:, 0]), atol=1e-9)
        c = field.moisture[:, -1]
        np.testing.assert_allclose(-7e-9*np.exp(-.89/c)*field.moisture_gradient_per_m[:, -1],
                                   8e-7*(c-room[:, 1]), atol=1e-15)

    def test_interpolant_matches_all_solver_midpoints(self):
        s = self.solution
        field = s.sample([17.5, 103.2], s.model.centers, coordinate='material')
        y = s.state([17.5, 103.2])
        np.testing.assert_allclose(field.temperature_K, y[:64].T, atol=1e-11)
        np.testing.assert_allclose(field.moisture, y[64:128].T, atol=1e-11)

    def test_irregular_times_and_repeated_positions(self):
        s = self.solution
        times = [120, 60, 0, 10.3, 60]
        field = s.sample(times, [.02, 0, .005, .005])
        for i, t in enumerate(times):
            other = s.sample(t, [.02, 0, .005, .005])
            np.testing.assert_allclose(field.temperature_K[i], other.temperature_K[0])
        np.testing.assert_allclose(field.moisture[:, 2], field.moisture[:, 3])

    def test_outside_points_are_explicitly_rejected_or_missing(self):
        with self.assertRaisesRegex(ValueError, '药材范围'):
            self.solution.sample([30], [.021])
        missing = self.solution.sample([30], [-.001, .01, .021], outside='nan')
        self.assertTrue(np.isnan(missing.moisture[0, [0, 2]]).all())
        self.assertTrue(np.isfinite(missing.moisture[0, 1]))
        for times in [[-1], [121], [np.nan], []]:
            with self.assertRaises(ValueError):
                self.solution.sample(times, [.01])

    def test_moving_radius_material_and_physical_sampling_agree(self):
        # Validates coordinate API, not the physical Q4 model or long-time event.
        s = solve_radial(16, appendix=4, shrink=True, duration_s=60)
        physical = s.sample([60], [s.model.radius(60)])
        material = s.sample([60], [1.], coordinate='material')
        np.testing.assert_allclose(physical.moisture, material.moisture)
        self.assertLess(material.radius_m[0, 0], .02)

    def test_kirchhoff_inverse_and_domain(self):
        c = np.geomspace(.01, 2.55, 40)
        for a in [.30, .45, .89]:
            np.testing.assert_allclose(inverse_kirchhoff(kirchhoff(c, a), a, 3.), c, atol=1e-12)
        with self.assertRaises(ValueError):
            inverse_kirchhoff([-1.], .89, 3.)

    def test_actual_temperature_forcing_matches_independent_modes(self):
        s = self.solution
        times, r = np.array([1., 20., 60., 100., 120.]), np.linspace(0, .02, 21)
        reference = heat_reference(s.model.room, times, r, modes=128)
        actual = s.sample(times, r).temperature_K-273.15
        self.assertLess(np.max(abs(reference-actual)), 5e-4)


if __name__ == '__main__':
    unittest.main()
