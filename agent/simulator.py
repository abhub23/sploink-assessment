import argparse
import httpx
import time
import random
import asyncio


BASE_URL = "http://localhost:8000"


async def send_event(
    session_id: str,
    step: int,
    action: str,
    input_text: str,
    output: str = "",
    file: str = None,
    status: str = "success",
):
    url = f"{BASE_URL}/events"

    metadata = {"status": status}
    if file:
        metadata["file"] = file

    payload = {
        "session_id": session_id,
        "timestamp": int(time.time()),
        "step": step,
        "action": action,
        "input": input_text,
        "output": output,
        "metadata": metadata,
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error sending event: {e}")
            return None


async def normal_scenario(session_id: str):
    print(f"Running normal scenario: {session_id}")

    files = ["utils.py", "models.py", "main.py", "config.json", "README.md"]

    events = [
        ("read_file", "src/utils.py", "Loading utilities", "utils.py"),
        ("llm_call", "Analyze project structure", "Found 5 modules", None),
        ("read_file", "src/models.py", "Loading models", "models.py"),
        ("llm_call", "Review model definitions", "3 models found", None),
        ("write_file", "src/api.py", "Created API endpoints", "api.py"),
        ("llm_call", "Add validation", "Validation added", None),
        ("run_command", "python -m pytest", "Tests passed", None),
        ("llm_call", "Check coverage", "85% coverage", None),
    ]

    for i, (action, inp, out, file) in enumerate(events):
        status = "success" if random.random() > 0.1 else "failure"
        await send_event(session_id, i + 1, action, inp, out, file, status)
        await asyncio.sleep(0.1)

    print(f"Normal scenario complete: {len(events)} events")


async def loop_scenario(session_id: str):
    print(f"Running loop scenario: {session_id}")

    attempts = 0
    step = 1

    base_patterns = [
        ("read_file", "src/utils.py", "Loading utils", "utils.py"),
        ("llm_call", "How do I fix this?", "Try checking line 42", None),
        ("read_file", "src/main.py", "Loading main", "main.py"),
    ]

    while attempts < 4:
        for i, (action, inp, out, file) in enumerate(base_patterns):
            variation = random.choice(["", "_v2", "_alt"])
            inp_var = inp + variation
            out_var = out + variation if variation else out

            await send_event(
                session_id, step, action, inp_var, out_var, file, "success"
            )
            await asyncio.sleep(0.05)
            step += 1

        attempts += 1

    print(f"Loop scenario complete: {step - 1} events")


async def drift_scenario(session_id: str):
    print(f"Running drift scenario: {session_id}")

    phase1 = [
        ("read_file", "src/frontend.tsx", "Loading frontend", "frontend.tsx"),
        ("llm_call", "Add dark mode", "Added theme toggle", None),
        ("write_file", "src/styles.css", "Updated CSS", "styles.css"),
    ]

    phase2 = [
        ("read_file", "src/backend.py", "Loading backend", "backend.py"),
        ("llm_call", "Add API endpoint", "Created route", None),
        ("run_command", "python manage.py migrate", "Migration run", None),
    ]

    phase3 = [
        ("read_file", "README.md", "Loading readme", "README.md"),
        ("write_file", "CHANGELOG.md", "Updated changelog", "CHANGELOG.md"),
    ]

    for i, e in enumerate(phase1):
        await send_event(session_id, i + 1, *e, "success")
        await asyncio.sleep(0.05)

    await asyncio.sleep(0.2)

    for i, e in enumerate(phase2):
        await send_event(session_id, i + 4, *e, "success")
        await asyncio.sleep(0.05)

    await asyncio.sleep(0.2)

    for i, e in enumerate(phase3):
        await send_event(session_id, i + 7, *e, "success")
        await asyncio.sleep(0.05)

    print(f"Drift scenario complete: 9 events")


async def failure_scenario(session_id: str):
    print(f"Running failure scenario: {session_id}")

    events = [
        ("run_command", "npm install", "Installing deps", None),
        ("run_command", "npm run build", "Build failed", None, "failure"),
        ("llm_call", "Fix build error", "Missing import", None, "failure"),
        ("read_file", "src/app.tsx", "File not found", None, "failure"),
        ("llm_call", "Debug the error", "Try reinstalling", None),
        ("run_command", "rm -rf node_modules", "Cleared cache", None),
        ("run_command", "npm install", "Reinstalled", None),
        ("run_command", "npm run build", "Build succeeded", None, "success"),
    ]

    for i, e in enumerate(events):
        if len(e) == 4:
            action, inp, out, file = e
            status = "success"
        else:
            action, inp, out, file, status = e

        await send_event(session_id, i + 1, action, inp, out, file, status)
        await asyncio.sleep(0.1)
        if status == "failure":
            await asyncio.sleep(0.2)

    print(f"Failure scenario complete: {len(events)} events")


SCENARIOS = {
    "normal": normal_scenario,
    "loop": loop_scenario,
    "drift": drift_scenario,
    "failure": failure_scenario,
}


async def main():
    parser = argparse.ArgumentParser(description="Agent Simulator")
    parser.add_argument("--scenario", choices=list(SCENARIOS.keys()), default="normal")
    parser.add_argument("--session-id", default=None)
    args = parser.parse_args()

    session_id = args.session_id or f"session_{args.scenario}_{int(time.time())}"

    scenario_func = SCENARIOS[args.scenario]
    await scenario_func(session_id)


if __name__ == "__main__":
    asyncio.run(main())
