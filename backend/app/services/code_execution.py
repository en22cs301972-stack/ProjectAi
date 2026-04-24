import asyncio
import subprocess
import tempfile
import os
import time
import resource
from typing import Optional, Tuple
from app.config import settings


LANGUAGE_CONFIG = {
    "python": {
        "extension": ".py",
        "run_cmd": ["python3", "-u"],
        "compile_cmd": None,
    },
    "java": {
        "extension": ".java",
        "run_cmd": ["java"],
        "compile_cmd": ["javac"],
    },
    "sql": {
        "extension": ".sql",
        "run_cmd": None,
        "compile_cmd": None,
    },
    "javascript": {
        "extension": ".js",
        "run_cmd": ["node"],
        "compile_cmd": None,
    },
}


async def execute_code(
    code: str,
    language: str,
    stdin: Optional[str] = None,
    timeout: int = None,
) -> dict:
    """Execute code in a sandboxed environment."""
    timeout = timeout or settings.CODE_EXECUTION_TIMEOUT

    if len(code) > settings.MAX_CODE_LENGTH:
        return {
            "status": "error",
            "output": None,
            "error": f"Code exceeds maximum length of {settings.MAX_CODE_LENGTH} characters",
            "execution_time": None,
            "memory_used": None,
        }

    if language not in LANGUAGE_CONFIG:
        return {
            "status": "error",
            "output": None,
            "error": f"Language '{language}' not supported",
            "execution_time": None,
            "memory_used": None,
        }

    config = LANGUAGE_CONFIG[language]

    if language == "sql":
        return await execute_sql(code)

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = f"solution{config['extension']}"
        if language == "java":
            # Java requires class name to match filename
            class_name = extract_java_class_name(code)
            filename = f"{class_name}.java"

        filepath = os.path.join(tmpdir, filename)
        with open(filepath, "w") as f:
            f.write(code)

        # Compile if needed
        if config["compile_cmd"]:
            compile_result = await run_process(
                config["compile_cmd"] + [filepath],
                cwd=tmpdir,
                timeout=30,
            )
            if compile_result["returncode"] != 0:
                return {
                    "status": "compile_error",
                    "output": None,
                    "error": compile_result["stderr"],
                    "execution_time": None,
                    "memory_used": None,
                }

        # Run
        if language == "java":
            class_name = extract_java_class_name(code)
            run_cmd = config["run_cmd"] + [class_name]
        else:
            run_cmd = config["run_cmd"] + [filepath]

        start_time = time.time()
        result = await run_process(
            run_cmd,
            cwd=tmpdir,
            timeout=timeout,
            stdin=stdin,
        )
        execution_time = time.time() - start_time

        if result.get("timed_out"):
            return {
                "status": "timeout",
                "output": None,
                "error": f"Code execution timed out after {timeout} seconds",
                "execution_time": execution_time,
                "memory_used": None,
            }

        if result["returncode"] != 0:
            return {
                "status": "runtime_error",
                "output": result.get("stdout", ""),
                "error": result.get("stderr", ""),
                "execution_time": execution_time,
                "memory_used": None,
            }

        return {
            "status": "success",
            "output": result.get("stdout", ""),
            "error": None,
            "execution_time": round(execution_time, 3),
            "memory_used": None,
        }


async def run_process(
    cmd: list,
    cwd: str = None,
    timeout: int = 30,
    stdin: str = None,
) -> dict:
    """Run a subprocess asynchronously."""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if stdin else None,
            cwd=cwd,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=stdin.encode() if stdin else None),
                timeout=timeout,
            )
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "timed_out": False,
            }
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {"returncode": -1, "stdout": "", "stderr": "", "timed_out": True}

    except Exception as e:
        return {"returncode": -1, "stdout": "", "stderr": str(e), "timed_out": False}


def extract_java_class_name(code: str) -> str:
    """Extract the main public class name from Java code."""
    import re
    match = re.search(r"public\s+class\s+(\w+)", code)
    if match:
        return match.group(1)
    return "Main"


async def execute_sql(code: str) -> dict:
    """Execute SQL code using SQLite for sandboxed execution."""
    import sqlite3
    import io

    output = io.StringIO()
    try:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        statements = [s.strip() for s in code.split(";") if s.strip()]
        results = []

        for stmt in statements:
            try:
                cursor.execute(stmt)
                if cursor.description:
                    columns = [d[0] for d in cursor.description]
                    rows = cursor.fetchall()
                    results.append(f"Columns: {', '.join(columns)}")
                    for row in rows:
                        results.append(str(row))
                else:
                    results.append(f"Query executed. Rows affected: {cursor.rowcount}")
            except sqlite3.Error as e:
                return {
                    "status": "runtime_error",
                    "output": "\n".join(results),
                    "error": str(e),
                    "execution_time": None,
                    "memory_used": None,
                }

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "output": "\n".join(results),
            "error": None,
            "execution_time": None,
            "memory_used": None,
        }

    except Exception as e:
        return {
            "status": "error",
            "output": None,
            "error": str(e),
            "execution_time": None,
            "memory_used": None,
        }


async def run_test_cases(code: str, language: str, test_cases: list) -> list:
    """Run code against test cases and return results."""
    results = []
    for i, test_case in enumerate(test_cases):
        result = await execute_code(
            code=code,
            language=language,
            stdin=test_case.get("input", ""),
        )
        expected = test_case.get("expected_output", "").strip()
        actual = (result.get("output") or "").strip()
        passed = actual == expected

        results.append({
            "test_case": i + 1,
            "passed": passed,
            "expected": expected,
            "actual": actual,
            "status": result["status"],
            "error": result.get("error"),
        })

    return results
