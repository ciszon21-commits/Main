"""Bounded MCP client. Supplied call files may run explicitly authorized mutations."""
import argparse
import json
import queue
import subprocess
import threading
from pathlib import Path


def check_response(response):
    """A JSON-RPC response can still contain a failed Rhino script."""
    if 'error' in response:
        raise RuntimeError(str(response['error']))
    result = response.get('result', {})
    if result.get('isError'):
        raise RuntimeError('MCP tool returned isError: ' + str(result.get('content')))
    for block in result.get('content', []):
        if block.get('type') != 'text':
            continue
        try:
            data = json.loads(block['text'])
        except (ValueError, KeyError):
            continue
        payload = data.get('payload', data) if isinstance(data, dict) else data
        if isinstance(payload, str) and (payload.startswith('Rhino.Runtime.Code.Execution.ExecuteException:')
                                        or payload.startswith('Traceback (most recent call last):')):
            raise RuntimeError(payload)
        if isinstance(payload, dict) and payload.get('error'):
            raise RuntimeError(str(payload.get('message', payload['error'])))


def probe(router, timeout, calls_path=None):
    process = subprocess.Popen(
        [str(router)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    messages = queue.Queue()
    errors = []

    def read_messages():
        for line in process.stdout:
            try:
                messages.put(json.loads(line))
            except ValueError:
                messages.put({"transport_text": line.strip()})
        messages.put({'transport_closed': True})

    def read_errors():
        for line in process.stderr:
            errors.append(line.rstrip())

    threading.Thread(target=read_messages, daemon=True).start()
    threading.Thread(target=read_errors, daemon=True).start()
    transcript = []

    def rpc(method, params, request_id):
        process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id,
                                       "method": method, "params": params}) + "\n")
        process.stdin.flush()
        import time
        deadline = time.monotonic() + timeout
        while True:
            item = messages.get(timeout=max(0.01, deadline - time.monotonic()))
            transcript.append(item)
            if item.get('transport_closed'):
                raise RuntimeError('MCP router exited before responding; inspect stderr')
            if item.get("id") == request_id:
                return item
            if time.monotonic() >= deadline:
                raise queue.Empty

    report = {"router": str(router), "status": "UNVERIFIED"}
    try:
        initial = rpc("initialize", {"protocolVersion": "2024-11-05",
                      "capabilities": {}, "clientInfo": {
                          "name": "environmental-hub-audit", "version": "0.1"}}, 1)
        if "error" in initial:
            raise RuntimeError(str(initial["error"]))
        process.stdin.write(json.dumps({"jsonrpc": "2.0",
                              "method": "notifications/initialized"}) + "\n")
        process.stdin.flush()
        listing = rpc("tools/list", {}, 2)
        check_response(listing)
        report["tools"] = listing
        names = {t["name"] for t in listing.get("result", {}).get("tools", [])}
        if calls_path:
            calls = json.loads(calls_path.read_text(encoding="utf-8"))
            report["calls"] = []
            for index, call in enumerate(calls, start=3):
                if call["name"] not in names:
                    raise ValueError("Tool unavailable: " + call["name"])
                response = rpc("tools/call", call, index)
                report["calls"].append({"name": call["name"], "response": response})
                check_response(response)
        elif "list_slots" in names:
            report["slots"] = rpc("tools/call", {
                "name": "list_slots", "arguments": {}}, 3)
            check_response(report['slots'])
        report["status"] = "MCP_RESPONDED"
    except queue.Empty:
        report["error"] = "MCP response timeout"
    except Exception as exc:
        report["error"] = str(exc)
    finally:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        report["stderr"] = errors
        report["transcript"] = transcript
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("router", type=Path)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--calls", type=Path)
    args = parser.parse_args()
    result = probe(args.router, args.timeout, args.calls)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "error": result.get("error"),
                      "output": str(args.output),
                      "call_count": len(result.get("calls", []))}, ensure_ascii=False))
    if result.get('error'):
        raise SystemExit(1)
