
from backend.app.services.analytics_service import get_vibe_score_over_time, get_vibe_score_trend

async def build_vibe_score_kpi(db, business_id: int):
    history = await get_vibe_score_over_time(db, business_id, "monthly")
    trend = await get_vibe_score_trend(db, business_id)

    data = history["data"]

    if len(data) < 2:
        return {
            "status": "insufficient_data",
            "current_score": None,
            "trend": "insufficient_data",
            "change": 0,
            "timeseries": data
        }

    current = data[-1]["avg_score"]
    previous = data[-2]["avg_score"]

    change = current - previous
    change_percent = (change / previous * 100) if previous != 0 else 0

    return {
        "status": "computed",
        "current_score": current,
        "previous_score": previous,
        "change": change,
        "change_percent": change_percent,
        "trend": trend["trend"],
        "slope": trend["slope"],
        "timeseries": [
            {"period": d["period"], "value": d["avg_score"]}
            for d in data
        ]
    }