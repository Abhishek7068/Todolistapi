from bson.errors import InvalidId
from click.testing import Result
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

MONGO_URI = "mongodb+srv://KingLycan:GXwluIY8wGVgfAc3@listtodo.zyjel.mongodb.net/"
client = AsyncIOMotorClient(MONGO_URI)
db = client.todoList
collection = db.todos

class Todo(BaseModel):
    task: str
    date: str
    completed: bool = False

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the To-Do List API",
        "endpoints": {
            "Create": "POST /todo",
            "Read": "GET /todo",
            "Update": "PUT /todo/{task_id}",
            "Delete": "DELETE /todo/{task_id}"
        }
    }

# Create (Add Task)
@app.post("/todos")
async def add_task(todo: Todo):
    todo_dict = todo.dict()
    result = await collection.insert_one(todo_dict)
    created_task = await collection.find_one({"_id": result.inserted_id})
    created_task["_id"] = str(created_task["_id"])
    return created_task

# Read (Get All Tasks)
@app.get("/todos")
async def get_tasks():
    tasks = []
    async for task in collection.find().sort("_id", -1): #this ensures the newest first(descending)
        task["_id"] = str(task["_id"])
        tasks.append(task)
    return tasks

# Update (Modify Task)
@app.put("/todos/{task_id}")
async def update_task(task_id: str, updated_task: Todo):
    result = await collection.update_one({"_id": ObjectId(task_id)}, {"$set": updated_task.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task updated"}

# Delete (Remove Task)
@app.delete("/todos/{task_id}")
async def delete_task(task_id: str):
    result = await collection.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}


#additonal for toggle
@app.put("/todos/{task_id}/toggle")
async def toggle_task_completion(task_id: str):
    task = await collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    new_completed_status = not task.get("completed", False)
    result = await collection.update_one(
        {"_id": ObjectId(task_id)}, {"$set": {"completed": new_completed_status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"_id": task_id, "completed": new_completed_status}
