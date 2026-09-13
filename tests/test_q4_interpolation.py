"""半径插值试验不能改变同一进程中后续求解的默认半径。"""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code/common'))
sys.path.insert(0, str(ROOT / 'code/q4'))

from model import RadialModel
import q4_interpolation_sensitivity as interpolation


class RadiusIsolationTests(unittest.TestCase):
    def test_successful_cases_restore_radius(self):
        original = RadialModel.radius
        for kind in ('linear', 'pchip'):
            with self.subTest(kind=kind):
                result = interpolation.run_case(kind, 8)
                self.assertEqual(result['interpolator'], kind)
                self.assertGreater(result['event_time_h'], 0)
                self.assertLess(result['event_time_h'], 72)
                self.assertIs(RadialModel.radius, original)

    def test_solver_and_event_failures_restore_radius_and_propagate(self):
        original = RadialModel.radius
        for kind in ('linear', 'pchip'):
            for stage in ('solve_radial', 'locate_event'):
                with self.subTest(kind=kind, stage=stage):
                    failure = RuntimeError('injected numerical failure')
                    # 不运行长时间积分，只检验异常的传播和共享状态恢复。
                    with patch.object(interpolation, 'solve_radial'):
                        with patch.object(interpolation, stage, side_effect=failure):
                            with self.assertRaises(RuntimeError) as caught:
                                interpolation.run_case(kind, 8)
                    self.assertIs(caught.exception, failure)
                    self.assertIs(RadialModel.radius, original)

    def test_invalid_kind_keeps_radius_unchanged(self):
        original = RadialModel.radius
        with self.assertRaisesRegex(ValueError, '插值方法'):
            interpolation.run_case('unknown', 8)
        self.assertIs(RadialModel.radius, original)


if __name__ == '__main__':
    unittest.main()
