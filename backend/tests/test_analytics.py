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

    result = await AnalyticsService.get_sentiment_over_time(
        db, business_id=1, granularity="monthly"
    )

    assert "data" in result
    assert len(result["data"]) == 2
    assert result["data"][0]["period"]
    assert "avg_score" in result["data"][0]
    assert "meta" in result


@pytest.mark.asyncio
async def test_sentiment_distribution():
    db = FakeDB([
        FakeRow(sentiment_label="positive", count=3),
        FakeRow(sentiment_label="negative", count=1),
    ])

    result = await AnalyticsService.get_sentiment_distribution(db, 1)

    assert result["total_reviews"] == 4
    assert "distribution" in result
    assert "meta" in result
    assert result["distribution"]["positive"]["count"] == 3
    assert result["distribution"]["negative"]["count"] == 1


@pytest.mark.asyncio
async def test_sentiment_trend():
    db = FakeDB([
        FakeRow(date="2026-01-01", avg_score=-0.5),
        FakeRow(date="2026-01-02", avg_score=0.0),
        FakeRow(date="2026-01-03", avg_score=0.5),
        FakeRow(date="2026-01-04", avg_score=0.7),
        FakeRow(date="2026-01-05", avg_score=0.8),
    ])

    result = await AnalyticsService.get_sentiment_trend_slope(db, 1)

    assert result["trend"] == "improving"
    assert result["slope"] > 0
    assert "meta" in result


@pytest.mark.asyncio
async def test_volatility():
    db = FakeDB([
        FakeRow(0.9),
        FakeRow(0.85),
        FakeRow(0.88),
        FakeRow(0.87),
        FakeRow(0.89),
    ])

    result = await AnalyticsService.get_sentiment_volatility(db, 1)

    assert "stability" in result
    assert result["stability"] in ["stable", "unstable"]
    assert "meta" in result


@pytest.mark.asyncio
async def test_peak_drop():
    db = FakeDB([
        FakeRow(date="2026-01-01", avg_score=0.1),
        FakeRow(date="2026-01-02", avg_score=0.8),
        FakeRow(date="2026-01-03", avg_score=-0.5),
        FakeRow(date="2026-01-04", avg_score=0.2),
        FakeRow(date="2026-01-05", avg_score=0.3),
    ])

    result = await AnalyticsService.get_peak_and_drop(db, 1)

    assert result["peak"]["change"] > 0
    assert result["drop"]["change"] < 0
    assert "meta" in result


@pytest.mark.asyncio
async def test_forecast():
    db = FakeDB([
        FakeRow(period="2026-01", avg_score=-0.5),
        FakeRow(period="2026-02", avg_score=0.0),
        FakeRow(period="2026-03", avg_score=0.5),
        FakeRow(period="2026-04", avg_score=0.3),
        FakeRow(period="2026-05", avg_score=0.4),
        FakeRow(period="2026-06", avg_score=0.6),
    ])

    result = await AnalyticsService.forecast_sentiment(db, 1)

    assert "forecast_score" in result
    assert "predicted_vibe" in result
    assert "meta" in result


@pytest.mark.asyncio
async def test_business_aspect_summary():

    db = FakeDB([
        FakeRow(aspect="service", avg_score=0.6, count=3),
        FakeRow(aspect="food", avg_score=-0.3, count=2),
        FakeRow(aspect="cleanliness", avg_score=0.1, count=5),
    ])

    result = await AnalyticsService.get_business_aspect_summary(db, 1)

    assert "summary" in result
    assert "service" in result["summary"]
    assert result["summary"]["service"]["label"] == "positive"
    assert result["summary"]["food"]["label"] == "negative"
    assert result["summary"]["cleanliness"]["label"] == "neutral"
    assert "meta" in result


@pytest.mark.asyncio
async def test_vibe_score_trend():
    db = FakeDB([
        FakeRow(snapshot_date=datetime.datetime(2026, 1, 1), vibe_score=1.1),
        FakeRow(snapshot_date=datetime.datetime(2026, 1, 2), vibe_score=2.4),
        FakeRow(snapshot_date=datetime.datetime(2026, 1, 3), vibe_score=3.0),
        FakeRow(snapshot_date=datetime.datetime(2026, 1, 4), vibe_score=3.5),
        FakeRow(snapshot_date=datetime.datetime(2026, 1, 5), vibe_score=4.0),
        FakeRow(snapshot_date=datetime.datetime(2026, 1, 6), vibe_score=4.2),
        FakeRow(snapshot_date=datetime.datetime(2026, 1, 7), vibe_score=4.5),
    ])

    result = await AnalyticsService.get_vibe_score_trend(db, 1)

    assert result["trend"] == "improving"
    assert result["slope"] > 0
    assert "meta" in result


@pytest.mark.asyncio
async def test_vibe_volatility():
    db = FakeDB([
        FakeRow(3.9),
        FakeRow(3.85),
        FakeRow(3.87),
        FakeRow(3.88),
        FakeRow(3.89),
    ])

    result = await AnalyticsService.get_vibe_volatility(db, 1)

    assert "volatility" in result
    assert result["stability"] in ["stable", "unstable"]
    assert "meta" in result


@pytest.mark.asyncio
async def test_latest_vibe():
    db = FakeDB([
        FakeRow(vibe_score=0.2, vibe_label="neutral", snapshot_date="2026-01-01")
    ])

    result = await AnalyticsService.get_latest_vibe(db, 1)

    assert result["vibe_score"] == 0.2
    assert result["vibe_label"] == "neutral"