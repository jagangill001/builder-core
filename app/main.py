from fastapi import FastAPI

app = FastAPI(title="Builder Core")

@app.get("/")
def home():
    return {"status": "Builder Core Running"}
