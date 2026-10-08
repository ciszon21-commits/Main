"""Verify fail-fast handling of real MCP response envelopes without launching Rhino."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from mcp_probe import check_response, bind_owned_call


def envelope(payload):
    return {'result': {'content': [{'type': 'text', 'text': json.dumps({'payload': payload})}]}}


class ResponseChecks(unittest.TestCase):
    def test_owned_binding_requires_explicit_spawn(self):
        for owned in [None, {'adopted': True, 'pid': 17, 'slotId': 'slot'}, {'adopted': False, 'pid': 0, 'slotId': 'slot'}]:
            with self.assertRaises(ValueError):
                bind_owned_call({'arguments': {'slot': '$owned'}}, owned)

    def test_owned_binding_preserves_template_and_quotes_slot(self):
        call = {'name': 'run_python', 'arguments': {'slot': '$owned', 'script': 'pid=__OWNED_PID__; slot=__OWNED_SLOT__'}}
        bound = bind_owned_call(call, {'adopted': False, 'pid': 17, 'slotId': "slot'quote"})
        self.assertEqual(call['arguments']['slot'], '$owned')
        self.assertEqual(bound['arguments']['slot'], "slot'quote")
        namespace = {}
        exec(bound['arguments']['script'], namespace)
        self.assertEqual(namespace['pid'], 17)
        self.assertEqual(namespace['slot'], "slot'quote")

    def test_explicit_target_remains_unchanged(self):
        call = {'arguments': {'slot': 'explicit'}}
        self.assertIs(bind_owned_call(call, None), call)

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

    def test_stdout_then_rhino_exception(self):
        with self.assertRaisesRegex(RuntimeError, 'not implemented'):
            check_response(envelope('{"objects": 0}\r\nRhino.Runtime.Code.Execution.ExecuteException: The method or operation is not implemented.\r\n ---> System.NotImplementedException'))

    def test_stdout_then_traceback(self):
        with self.assertRaisesRegex(RuntimeError, 'AssertionError'):
            check_response(envelope('Starting validation\n\nTraceback (most recent call last):\nAssertionError: wrong dock container'))

    def test_unwrapped_text_exception(self):
        with self.assertRaisesRegex(RuntimeError, 'Wrong release'):
            check_response({'result': {'content': [{'type': 'text', 'text': 'Starting\nRhino.Runtime.Code.Execution.ExecuteException: Wrong release'}]}})

    def test_quoted_diagnostic_name_is_successful_data(self):
        check_response(envelope('{"expected_error": "Rhino.Runtime.Code.Execution.ExecuteException: example"}'))


if __name__ == '__main__':
    unittest.main()
