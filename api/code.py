from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import numpy as np
import json
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

class TelemetryRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

def load_telemetry_data():
    path = Path("telemetry.json")
    with open(path, "r") as f:
        return json.load(f)

telemetry_records = load_telemetry_data()

@app.post("/latency-metrics")
async def latency_metrics(request: TelemetryRequest):
    response = {}
    for region in request.regions:
        region_data = [r for r in telemetry_records if r.get("region") == region]
        if not region_data:
            response[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0,
            }
            continue
        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime_percent"] for r in region_data]

        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        avg_uptime = np.mean(uptimes)
        breaches = sum(1 for l in latencies if l > request.threshold_ms)

        response[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": breaches,
        }

    return response
