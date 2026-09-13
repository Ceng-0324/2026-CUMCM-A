"""保护输入与数值迁移中的关键数学不变量。"""
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import numpy as np
from scipy.integrate import quad

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code/common'))
from audit import audit_inputs
from data_io import verify_inputs
from model import analytic_radial_check, divergence, kirchhoff, material_parameters, probe_a, radial_geometry, solve_radial


class InputTests(unittest.TestCase):
    def test_original_inputs_and_time_grids(self):
        audit = audit_inputs()
        self.assertEqual(audit['files_verified'], 7)
        self.assertEqual(audit['room']['first'], {1: 0., 2: 28., 3: .01963})
        self.assertEqual(audit['radius']['last'], {1: 259200., 2: 1.198})

    def test_modified_original_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / 'problemA', root / 'problemA')
            target = root / 'problemA/附件/附件1.xlsx'
            target.write_bytes(target.read_bytes() + b'changed')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                verify_inputs(root)

    def test_audit_checks_the_requested_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / 'problemA', root / 'problemA')
            # A valid XLSX with the wrong layout must fail even if its hash matches.
            source = root / 'problemA/附件/附件2.xlsx'
            target = root / 'problemA/附件/附件1.xlsx'
            shutil.copyfile(source, target)
            manifest_path = root / 'problemA/manifest.json'
            manifest = json.loads(manifest_path.read_text())
            for entry in manifest['files']:
                if entry['path'] == 'problemA/附件/附件1.xlsx':
                    entry['sha256'] = sha256(target.read_bytes()).hexdigest()
                    entry['bytes'] = target.stat().st_size
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, '数据行数'):
                audit_inputs(root)


class NumericalTests(unittest.TestCase):
    def test_nonlinear_primitive_matches_independent_quadrature(self):
        for a in [.89, .45, .30]:
            for c in [.05, .15, 1., 2.55]:
                expected = quad(lambda s: np.exp(-a/s), 0, c, epsabs=1e-14)[0]
                self.assertAlmostEqual(kirchhoff(c, a), expected, delta=1e-12)

    def test_appendix_diffusivities_and_temperature_units(self):
        c = np.array([.05, .15, 2.55])
        for appendix, prefactor, a in [(2, 7e-9, .89), (3, 2.4e-3, .45), (4, 4.2e-4, .30)]:
            rho, cp, k, base, exponent = material_parameters(c, 323.15, appendix)
            actual = base*np.exp(-exponent/c)
            expected = prefactor*np.exp(-a/c)
            if appendix != 2:
                expected *= np.exp(-3850/323.15)
            np.testing.assert_allclose(actual, expected, rtol=1e-13)
            self.assertTrue(np.all(np.diff(actual) > 0))
            self.assertTrue(np.all(rho > 0) and np.all(cp > 0) and np.all(k > 0))
        _, _, _, base, a = material_parameters(.15, 323.15, 3)
        self.assertAlmostEqual(base*np.exp(-a/.15), 8.0012e-10, delta=1e-14)

    def test_radial_flux_telescopes_to_boundary_loss(self):
        for n in [7, 32]:
            edges, _, weights = radial_geometry(n)
            flux = np.random.default_rng(n).normal(size=n+1)
            flux[0] = 0
            for radius in [.02, .013]:
                change = 2*weights @ divergence(flux, radius, edges, weights)
                self.assertAlmostEqual(change, -2*flux[-1]/radius, delta=1e-10)

    def test_constant_diffusion_has_second_order_spatial_convergence(self):
        errors = [analytic_radial_check(n)['max_error'] for n in [16, 32, 64]]
        for coarse, fine in zip(errors, errors[1:]):
            self.assertGreater(coarse/fine, 3.5)
            self.assertLess(coarse/fine, 4.5)

    def test_q1_short_run_preserves_positive_moisture_and_balance(self):
        run = probe_a(16, appendix=2, max_hours=.5)
        self.assertTrue(run['success'])
        self.assertIsNone(run['drying_event_hours'])
        self.assertGreater(run['min_C'], 0)
        self.assertLess(run['max_dry_mass_normalized_balance_residual'], 1e-10)
        self.assertGreater(run['samples']['0.5']['center_T_C'], 28)

    def test_invalid_solver_configuration_is_rejected(self):
        for kwargs in [{'n': 3}, {'n': 8, 'rtol': 0}, {'n': 8, 'boundary': 'unknown'}]:
            with self.assertRaises(ValueError):
                probe_a(**kwargs)
        with self.assertRaises(ValueError):
            material_parameters(1., 300., 1)
        with self.assertRaisesRegex(ValueError, '时间积分方法'):
            solve_radial(8, duration_s=1, method='CrankNicolson')


if __name__ == '__main__':
    unittest.main()
