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