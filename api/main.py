# api/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from tasks.worker import run_task



app = FastAPI()

class InputData(BaseModel):
    x: int
    y: int

@app.post("/add")
async def add(data: InputData):
    task = run_task.delay(data.x, data.y)
    return {"task_id": task.id}
