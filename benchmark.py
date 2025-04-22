import asyncio
import httpx
import time
import argparse
import os
from typing import List, Dict, Any

API_BASE_URL = "http://127.0.0.1:8000"  # Assuming the API runs locally on port 8000

async def poll_status(client: httpx.AsyncClient, job_id: str, timeout: int = 120) -> Dict[str, Any]:
    """Polls the job status endpoint until completion or timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = await client.get(f"{API_BASE_URL}/status/{job_id}")
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            if data.get("status") in ["completed", "failed"]:
                return data
        except httpx.RequestError as e:
            print(f"Error polling job {job_id}: {e}")
            # Decide if you want to retry or fail immediately
            await asyncio.sleep(1) # Wait a bit before retrying on network errors
        except Exception as e:
            print(f"Unexpected error polling job {job_id}: {e}")
            return {"status": "failed", "error": f"Polling error: {e}"}

        await asyncio.sleep(0.5)  # Wait before polling again

    print(f"Timeout waiting for job {job_id}")
    return {"status": "failed", "error": "Timeout"}


async def run_single_job(client: httpx.AsyncClient, payload: Dict[str, Any]) -> float:
    """Sends a generation request and waits for completion, returning duration."""
    start_time = time.time()
    job_id = None
    try:
        response = await client.post(f"{API_BASE_URL}/generate", json=payload)
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data.get("job_id")

        if not job_id:
            print("Failed to get job_id from response")
            return -1.0 # Indicate failure

        final_status = await poll_status(client, job_id)

        if final_status.get("status") != "completed":
            print(f"Job {job_id} failed or timed out: {final_status.get('error', 'Unknown error')}")
            return -1.0 # Indicate failure

        # Optional: Cleanup
        # await client.delete(f"{API_BASE_URL}/jobs/{job_id}")

    except httpx.RequestError as e:
        print(f"Request failed: {e}")
        return -1.0 # Indicate failure
    except Exception as e:
        print(f"An unexpected error occurred for job {job_id or 'unknown'}: {e}")
        return -1.0 # Indicate failure
    finally:
        # Ensure cleanup even if polling fails but job_id was obtained
        if job_id:
             try:
                 await client.delete(f"{API_BASE_URL}/jobs/{job_id}")
             except Exception as cleanup_err:
                 print(f"Error cleaning up job {job_id}: {cleanup_err}")


    end_time = time.time()
    return end_time - start_time


async def run_benchmark(num_concurrent: int):
    """Runs the benchmark with N concurrent requests."""
    payload = {
        "wordlist": ["BENCHMARK", "TEST", "CONCURRENT", "FASTAPI", "PYTHON", "ASYNCIO", "HTTPX", "PARALLEL"],
        "size": 15 # Adjust size if needed, larger size = longer generation
    }

    print(f"Starting benchmark with {num_concurrent} concurrent requests...")
    start_total_time = time.time()

    async with httpx.AsyncClient(timeout=150.0) as client: # Increase client timeout
        tasks = [run_single_job(client, payload) for _ in range(num_concurrent)]
        results = await asyncio.gather(*tasks)

    end_total_time = time.time()
    total_duration = end_total_time - start_total_time

    successful_jobs = [duration for duration in results if duration > 0]
    failed_jobs = len(results) - len(successful_jobs)
    num_successful = len(successful_jobs)

    print("\n--- Benchmark Results ---")
    print(f"Total concurrent requests: {num_concurrent}")
    print(f"Successful jobs: {num_successful}")
    print(f"Failed/Timed out jobs: {failed_jobs}")

    if num_successful > 0:
        average_latency = sum(successful_jobs) / num_successful
        throughput = num_successful / total_duration if total_duration > 0 else 0
        print(f"Total time for all requests: {total_duration:.2f} seconds")
        print(f"Average job latency (for successful jobs): {average_latency:.2f} seconds")
        print(f"Throughput: {throughput:.2f} jobs/second")
    else:
        print("No jobs completed successfully.")
        print(f"Total time elapsed: {total_duration:.2f} seconds")

    print("-------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark FastAPI puzzle generation API.")
    parser.add_argument("-n", "--num", type=int, default=max(1, os.cpu_count() or 1),
                        help="Number of concurrent requests to send.")
    args = parser.parse_args()

    asyncio.run(run_benchmark(args.num))
