import datetime

import pytest
from backend.app.services.analytics_service import AnalyticsService


class FakeRow:
    def __init__(self, *args, **kwargs):
        self._values = args
        self.__dict__.update(kwargs)

    def __getitem__(self, item):
        # supports r[0]
        if isinstance(item, int):
            return self._values[item]
        # supports r["field"]
        return getattr(self, item)

    def __getattr__(self, name):
        return self.__dict__.get(name)


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def __iter__(self):
        return iter(self._rows)
    
    def scalar_one_or_none(self):
        if not self._rows:
            return None
        return self._rows[0]


class FakeDB:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, stmt):
        return FakeResult(self._rows)


@pytest.mark.asyncio
async def test_temporal_aggregation():
    db = FakeDB([
        FakeRow(period="2026-01", avg_score=0.5, count=2),
        FakeRow(period="2026-02", avg_score=-0.2, count=3),
    ])

    result = await AnalyticsService.get_temporal_aggregation(
        db, business_id=1, granularity="monthly"
    )

    assert len(result) == 2
    assert result[0]["period"]
    assert "avg_score" in result[0]


@pytest.mark.asyncio
async def test_sentiment_distribution():
    db = FakeDB([
        FakeRow(sentiment_label="positive", count=3),
        FakeRow(sentiment_label="negative", count=1),
    ])

    result = await AnalyticsService.get_sentiment_distribution(db, 1)

    assert result["total"] == 4
    assert result["distribution"]["positive"] == 3
    assert result["distribution"]["negative"] == 1


@pytest.mark.asyncio
async def test_sentiment_trend():
    db = FakeDB([
        FakeRow(avg_score=-0.5),
        FakeRow(avg_score=0.0),
        FakeRow(avg_score=0.5),
    ])

    result = await AnalyticsService.get_sentiment_trend_slope(db, 1)

    assert result["trend"] == "improving"
    assert result["slope"] > 0


@pytest.mark.asyncio
async def test_volatility():
    db = FakeDB([
        FakeRow(0.9),
        FakeRow(0.85),
        FakeRow(0.88),
    ])

    result = await AnalyticsService.get_sentiment_volatility(db, 1)

    assert result["stability"] == "stable"


@pytest.mark.asyncio
async def test_peak_drop():
    db = FakeDB([
        FakeRow(date="2026-01-01", avg_score=0.1),
        FakeRow(date="2026-01-02", avg_score=0.8),
        FakeRow(date="2026-01-03", avg_score=-0.5),
    ])

    result = await AnalyticsService.get_peak_and_drop(db, 1)

    assert result["peak"]["change"] > 0
    assert result["drop"]["change"] < 0


@pytest.mark.asyncio
async def test_forecast():
    db = FakeDB([
        FakeRow(period="2026-01", avg_score=-0.5),
        FakeRow(period="2026-02", avg_score=0.0),
        FakeRow(period="2026-03", avg_score=0.5),
    ])

    result = await AnalyticsService.forecast_sentiment(db, 1)

    assert "forecast_score" in result
    assert "predicted_vibe" in result


@pytest.mark.asyncio
async def test_business_aspect_summary():

    db = FakeDB([
        FakeRow(aspect="service", avg_score=0.6, count=3),
        FakeRow(aspect="food", avg_score=-0.3, count=2),
        FakeRow(aspect="cleanliness", avg_score=0.1, count=5),
    ])

    result = await AnalyticsService.get_business_aspect_summary(db, 1)

    assert "service" in result
    assert result["service"]["label"] == "positive"

    assert result["food"]["label"] == "negative"
    assert result["cleanliness"]["label"] == "neutral"


@pytest.mark.asyncio
async def test_vibe_score_trend():
    db = FakeDB([
        FakeRow(snapshot_date=datetime.datetime(2026, 1, 1), vibe_score=0.1),
        FakeRow(snapshot_date=datetime.datetime(2026, 1, 2), vibe_score=0.4),
        FakeRow(snapshot_date=datetime.datetime(2026, 1, 3), vibe_score=0.8),
    ])

    result = await AnalyticsService.get_vibe_score_trend(db, 1)

    assert result["trend"] == "improving"
    assert result["slope"] > 0


@pytest.mark.asyncio
async def test_vibe_volatility():
    db = FakeDB([
        FakeRow(0.9),
        FakeRow(0.85),
        FakeRow(0.87),
    ])

    result = await AnalyticsService.get_vibe_volatility(db, 1)

    assert "volatility" in result
    assert result["stability"] in ["stable", "unstable"]


@pytest.mark.asyncio
async def test_latest_vibe():
    db = FakeDB([
        FakeRow(vibe_score=0.2, vibe_label="neutral", snapshot_date="2026-01-01")
    ])

    result = await AnalyticsService.get_latest_vibe(db, 1)

    assert result["vibe_score"] == 0.2
    assert result["vibe_label"] == "neutral"