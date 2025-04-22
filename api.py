from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
import os
import json
import shutil
import asyncio
from concurrent.futures import ProcessPoolExecutor

from generatePuzzle import create_puzzle_and_solution
from index import create_title_page

# Create a process pool executor (adjust max_workers as needed)
process_pool = ProcessPoolExecutor(max_workers=os.cpu_count() or 1)

app = FastAPI()


#CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Output-Dir
os.makedirs('output', exist_ok=True)
os.makedirs('output/puzzles',exist_ok=True)

#In Memory Job store

puzzle_jobs = {}

class PuzzleRequest(BaseModel):
    wordlist: List[str]
    size: int = 15
    mask_type: Optional[str] = None
    book_name: str = "Where's Word-o"

class JobResponse(BaseModel):
    job_id: str
    status: str

def run_generation_in_process(job_folder: str, params: Dict):
    """Helper function to run the CPU-bound task in the process pool."""
    puzzle_filename = f"{job_folder}/puzzle"
    wordlist = params["wordlist"]
    size = params["size"]
    mask_type = params["mask_type"]

    # This function will run in a separate process
    create_puzzle_and_solution(
        puzzle_filename,
        wordlist,
        size,
        size,
        mask_type=mask_type,
        background_image=None,
        page_number=None
    )
    # Return necessary info for status update
    # Extract job_id from job_folder path for the URLs
    job_id = os.path.basename(job_folder)
    return {
        "puzzle_url": f"/output/puzzles/{job_id}/puzzle.svg",
        "solution_url": f"/output/puzzles/{job_id}/puzzleS.svg"
    }

async def generate_puzzle_task(job_id: str, params: Dict):
    job_folder = f"output/puzzles/{job_id}"
    os.makedirs(job_folder, exist_ok=True)
    loop = asyncio.get_running_loop()

    try:
        puzzle_jobs[job_id]["status"] = "processing"

        # Run the CPU-bound task in the process pool executor
        result = await loop.run_in_executor(
            process_pool, 
            run_generation_in_process, # Target function (now synchronous)
            job_folder, 
            params
        )

        puzzle_jobs[job_id]["status"] = "completed"
        puzzle_jobs[job_id]["result"] = result
        
    except Exception as e:
        print(f"Error processing job {job_id}: {e}") # Log the error
        puzzle_jobs[job_id]["status"] = "failed"
        puzzle_jobs[job_id]["error"] = str(e)
    finally:
        pass

@app.post("/generate", response_model=JobResponse)
async def generate_puzzle(request: PuzzleRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    
    puzzle_jobs[job_id] = {
        "status": "queued",
        "params": request.dict()
    }
    
    # Start generation in background
    background_tasks.add_task(generate_puzzle_task, job_id, request.dict())
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in puzzle_jobs:
        return {"status": "not_found"}
    
    return puzzle_jobs[job_id]

# Serve static files
app.mount("/output", StaticFiles(directory="output"), name="output")

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    if job_id in puzzle_jobs:
        # Remove the job data
        del puzzle_jobs[job_id]
        
        # Remove the job files
        job_folder = f"output/puzzles/{job_id}"
        if os.path.exists(job_folder):
            shutil.rmtree(job_folder)
        
        return {"status": "deleted"}
    return {"status": "not_found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)