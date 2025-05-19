import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.post("/segment")
async def segment():
    # TODO: implement ViT+SAM inference
    return {"dsl_version": "0.9", "tree": []}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
