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

from generatePuzzle import create_puzzle_and_solution
from index import create_title_page

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

async def generate_puzzle_task(job_id: str, params: Dict):
    job_folder = f"output/puzzles/{job_id}"
    os.makedirs(job_folder, exist_ok=True)

    try:
        puzzle_jobs[job_id]["status"] = "processing"

        #generation function call
        puzzle_filename = f"{job_folder}/puzzle"
        wordlist = params["wordlist"]
        size = params["size"]
        mask_type = params["mask_type"]

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            create_puzzle_and_solution,
            puzzle_filename,
            wordlist,
            size,
            size,
            mask_type,
            None,  # background_image
            None   # page_number
        )

        puzzle_jobs[job_id]["status"] = "completed"
        puzzle_jobs[job_id]["result"] = {
            "puzzle_url": f"/output/puzzles/{job_id}/puzzle.svg",
            "solution_url": f"/output/puzzles/{job_id}/puzzleS.svg"
        }
        
    except Exception as e:
        puzzle_jobs[job_id]["status"] = "failed"
        puzzle_jobs[job_id]["error"] = str(e)

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