"""Verify fail-fast handling of real MCP response envelopes without launching Rhino."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from mcp_probe import check_response


def envelope(payload):
    return {'result': {'content': [{'type': 'text', 'text': json.dumps({'payload': payload})}]}}


class ResponseChecks(unittest.TestCase):
    def test_success_object(self):
        check_response(envelope({'passed': 45}))

    def test_success_string(self):
        check_response(envelope('Visual state restored'))

    def test_slots_array(self):
        check_response(envelope([]))

    def test_jsonrpc_error(self):
        with self.assertRaises(RuntimeError):
            check_response({'error': {'code': -1, 'message': 'Failed'}})

    def test_mcp_error(self):
        with self.assertRaises(RuntimeError):
            check_response({'result': {'isError': True, 'content': []}})

    def test_nested_script_error(self):
        with self.assertRaisesRegex(RuntimeError, 'Wrong release'):
            check_response(envelope({'error': 'Failed', 'message': 'Wrong release'}))

    def test_string_exception(self):
        with self.assertRaisesRegex(RuntimeError, 'Guid format'):
            check_response(envelope('Rhino.Runtime.Code.Execution.ExecuteException: Unrecognized Guid format.'))

    def test_traceback_string(self):
        with self.assertRaises(RuntimeError):
            check_response(envelope('Traceback (most recent call last):\nAssertionError'))


if __name__ == '__main__':
    unittest.main()
