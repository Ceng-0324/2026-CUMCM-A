"""Q1 输出契约：数据、模板时间轴及显示精度。"""
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code/common'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code/q1'))
from data_io import ROOT
from problem1 import export_workbook, run, verify_workbook


class WorkbookTests(unittest.TestCase):
    def test_roundtrip_and_corrupted_time_axis(self):
        # Structured values expose column transposition and rounding errors.
        temperature = 28+np.arange(1800)[:, None]*.001+np.arange(21)[None, :]*.123456
        moisture = 2.55-np.arange(1800)[:, None]*.0001-np.arange(21)[None, :]*.010123
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'result1.xlsx'
            export_workbook(path, temperature, moisture)
            result = verify_workbook(path, temperature, moisture)
            self.assertEqual(result['numeric_field_cells'], 75600)
            with ZipFile(path) as archive:
                entries = {name: archive.read(name) for name in archive.namelist()}
            sheet = entries['xl/worksheets/sheet1.xml']
            self.assertIn(b'<c r="A2"><v>1</v></c>', sheet)
            entries['xl/worksheets/sheet1.xml'] = sheet.replace(b'<c r="A2"><v>1</v></c>',
                                                              b'<c r="A2"><v>0</v></c>')
            broken = Path(tmp)/'broken.xlsx'
            with ZipFile(broken, 'w') as archive:
                for name, content in entries.items():
                    archive.writestr(name, content)
            with self.assertRaises(AssertionError):
                verify_workbook(broken, temperature, moisture)

    def test_output_cannot_overwrite_input_directory(self):
        with self.assertRaisesRegex(ValueError, '禁止写入'):
            run(ROOT/'problemA/附件/附件3', ROOT/'reports/q1/RESULTS_REPORT.md')


if __name__ == '__main__':
    unittest.main()
