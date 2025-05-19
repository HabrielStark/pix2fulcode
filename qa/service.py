from fastapi import FastAPI

app = FastAPI()

@app.post("/qa")
async def qa():
    # TODO: pixel-diff and axe-core
    return {"delta": 0.0}
