import sys
import unittest
from pathlib import Path
import pyarrow as pa

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from dax_query import arrow_rows


def stream(table):
    sink=pa.BufferOutputStream()
    with pa.ipc.new_stream(sink,table.schema) as writer:
        writer.write_table(table)
    return sink.getvalue().to_pybytes()


class ArrowQueryTests(unittest.TestCase):
    def test_valid_kpi_row(self):
        table=pa.table({'[respondents]':[668665],'[yes]':[116779],'[no]':[551886]})
        self.assertEqual(arrow_rows(stream(table))[0]['[yes]'],116779)

    def test_http_200_error_rowset_is_failure(self):
        table=pa.table({'ErrorMessage':['denied']}).replace_schema_metadata({'IsError':'true','FaultString':'denied'})
        with self.assertRaisesRegex(RuntimeError,'denied'):
            arrow_rows(stream(table))

    def test_trailing_error_is_not_ignored(self):
        good=pa.table({'[respondents]':[668665]})
        error=pa.table({'ErrorMessage':['denied']}).replace_schema_metadata({'IsError':'true'})
        with self.assertRaises(RuntimeError):
            arrow_rows(stream(good)+stream(error))

    def test_truncated_response_is_not_accepted(self):
        with self.assertRaises(Exception):
            arrow_rows(b'invalid arrow stream')

    def test_multiple_rows_rejected(self):
        with self.assertRaises(ValueError):
            arrow_rows(stream(pa.table({'x':[1,2]})))


if __name__=='__main__':
    unittest.main()
