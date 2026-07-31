import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pythonjsonlogger.json import JsonFormatter

logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = FastAPI(title="Calculator API")

APP_VERSION = (
    open("VERSION").read().strip()
    if __import__("os").path.exists("VERSION")
    else "dev"
)


class CalculateRequest(BaseModel):
    operation: Literal["add", "sub", "mul", "div"]
    a: float
    b: float


class CalculateResponse(BaseModel):
    result: float
    operation: str
    a: float
    b: float


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/version")
def version():
    return {"version": APP_VERSION, "app": "calculator-api"}


@app.post("/calculate", response_model=CalculateResponse)
def calculate(req: CalculateRequest):
    ops = {
        "add": lambda a, b: a + b,
        "sub": lambda a, b: a - b,
        "mul": lambda a, b: a * b,
        "div": lambda a, b: a / b,
    }
    if req.operation == "div" and req.b == 0:
        raise HTTPException(status_code=400, detail="Division by zero")
    result = ops[req.operation](req.a, req.b)
    logger.info("calculate", extra={"operation": req.operation, "a": req.a, "b": req.b, "result": result})
    return CalculateResponse(result=result, operation=req.operation, a=req.a, b=req.b)
