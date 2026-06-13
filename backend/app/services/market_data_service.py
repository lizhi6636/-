"""Market data service — fetches from EastMoney, caches in Redis."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import akshare as ak
import pandas as pd

from app.core.celery_app import celery_app
from app.core.redis_client import cache_get, cache_set, cache_mget, cache_mset

logger = logging.getLogger(__name__)

# Cache TTL constants
REALTIME_TTL = 5  # 5 seconds for real-time quotes
KLINE_TTL = 3600  # 1 hour for K-line data
FUNDAMENTALS_TTL = 3600  # 1 hour for fundamentals
INDEX_TTL = 10  # 10 seconds for index data


async def get_realtime_quote(stock_code: str) -> Optional[dict]:
    """Get real-time quote for a single stock from Redis cache."""
    cached = await cache_get(f"quote:{stock_code}")
    if cached:
        return json.loads(cached)
    return None


async def get_realtime_quotes(stock_codes: list[str]) -> dict[str, dict]:
    """Get real-time quotes for multiple stocks from Redis cache, falling back to EastMoney."""
    keys = [f"quote:{code}" for code in stock_codes]
    results = await cache_mget(keys)
    quotes = {}
    missing = []
    for code, data in zip(stock_codes, results):
        if data:
            quotes[code] = json.loads(data)
        else:
            missing.append(code)

    # Fetch missing codes from EastMoney
    if missing:
        for code in missing:
            try:
                data = await asyncio.to_thread(_fetch_eastmoney_sync, code)
                if data and data.get("price", 0) > 0:
                    quotes[code] = data
                    await cache_set(f"quote:{code}", json.dumps(data), REALTIME_TTL)
            except Exception as e:
                logger.warning(f"Failed to fetch quote for {code}: {e}")

    return quotes


async def fetch_realtime_from_akshare(stock_code: str) -> Optional[dict]:
    """Fetch real-time quote from EastMoney API and cache it."""
    try:
        # Call EastMoney API directly (single stock, fast)
        data = await asyncio.to_thread(_fetch_eastmoney_sync, stock_code)

        if data and data.get("price", 0) > 0:
            await cache_set(f"quote:{stock_code}", json.dumps(data), REALTIME_TTL)
            return data
        return None

    except Exception as e:
        logger.error(f"Failed to fetch realtime data for {stock_code}: {e}")
        return None


def _fetch_eastmoney_sync(stock_code: str) -> Optional[dict]:
    """Synchronous EastMoney API call with multi-endpoint fallback.

    Tries multiple URLs in order — some endpoints are unreliable via Docker/Python.
    """
    import subprocess
    import json as _json

    market = "1" if stock_code.startswith(("6", "5")) else "0"
    secid = f"{market}.{stock_code}"
    fields = "f43,f44,f45,f46,f47,f48,f50,f51,f52,f57,f58,f60,f116,f117,f162,f167,f168,f169,f170,f171"

    # Multiple fallback URLs — try each until one works
    urls = [
        f"http://push2delay.eastmoney.com/api/qt/stock/get?secid={secid}&fields={fields}",
        f"http://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields={fields}",
    ]
    curl_base = ["curl", "-s", "--connect-timeout", "5", "--max-time", "10",
                 "-H", "User-Agent: Mozilla/5.0"]

    for url in urls:
        try:
            args = curl_base + [url]
            result = subprocess.run(args, capture_output=True, text=True, timeout=12)
            if result.returncode != 0 or not result.stdout.strip():
                continue  # try next endpoint

            data = _json.loads(result.stdout)
            d = data.get("data", {})
            if not d or d.get("f43", 0) == 0:
                continue

            price = d.get("f43", 0) / 100
            pre_close = d.get("f60", 0) / 100 if d.get("f60") else 0
            change = price - pre_close if price and pre_close else 0
            change_pct = (change / pre_close * 100) if pre_close else 0

            return {
                "code": stock_code, "name": d.get("f58", ""), "price": price,
                "change": round(change, 3), "change_pct": round(change_pct, 3),
                "open": d.get("f46", 0) / 100 if d.get("f46") else 0,
                "high": d.get("f44", 0) / 100 if d.get("f44") else 0,
                "low": d.get("f45", 0) / 100 if d.get("f45") else 0,
                "pre_close": pre_close,
                "volume": d.get("f47", 0) or 0,
                "amount": d.get("f48", 0) or 0,
                "update_time": datetime.now().isoformat(),
            }
        except Exception:
            continue  # try next endpoint

    logger.warning(f"All endpoints failed for {stock_code}")
    return None


async def get_kline(
    stock_code: str,
    period: str = "daily",
    start_date: str = "",
    end_date: str = "",
    adjust: str = "qfq",
) -> list[dict]:
    """Get K-line data for a stock.

    Args:
        stock_code: 6-digit stock code
        period: "daily", "weekly", or "monthly"
        start_date: YYYYMMDD format
        end_date: YYYYMMDD format
        adjust: "qfq" (前复权), "hfq" (后复权), or "" (不复权)

    Returns:
        List of OHLCV records
    """
    cache_key = f"kline:{stock_code}:{period}:{adjust}:{start_date}:{end_date}"
    cached = await cache_get(cache_key)
    if cached:
        return json.loads(cached)

    try:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )

        if df is None or df.empty:
            return []

        # Normalize columns
        records = []
        for _, row in df.iterrows():
            records.append({
                "date": str(row.get("日期", "")),
                "open": float(row.get("开盘", 0)),
                "close": float(row.get("收盘", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "volume": int(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
                "amplitude": float(row.get("振幅", 0)) if "振幅" in row else 0,
                "change_pct": float(row.get("涨跌幅", 0)) if "涨跌幅" in row else 0,
                "change_amount": float(row.get("涨跌额", 0)) if "涨跌额" in row else 0,
                "turnover": float(row.get("换手率", 0)) if "换手率" in row else 0,
            })

        await cache_set(cache_key, json.dumps(records), KLINE_TTL)
        return records

    except Exception as e:
        logger.error(f"Failed to fetch kline for {stock_code}: {e}")
        return []


async def get_stock_info(stock_code: str) -> Optional[dict]:
    """Get basic stock information (PE, PB, market cap, etc.)."""
    cache_key = f"info:{stock_code}"
    cached = await cache_get(cache_key)
    if cached:
        return json.loads(cached)

    try:
        df = ak.stock_individual_info_em(symbol=stock_code)
        if df is None or df.empty:
            return None

        info = {}
        for _, row in df.iterrows():
            key = str(row.get("item", ""))
            value = str(row.get("value", ""))
            info[key] = value

        result = {
            "code": stock_code,
            "name": info.get("股票简称", ""),
            "market": "上海" if stock_code.startswith(("6", "5")) else ("北京" if stock_code.startswith(("4", "8", "9")) else "深圳"),
            "pe": _safe_float(info.get("市盈率-动态")),
            "pb": _safe_float(info.get("市净率")),
            "market_cap": _safe_float(info.get("总市值")),
            "total_shares": _safe_int(info.get("总股本")),
        }

        await cache_set(cache_key, json.dumps(result), FUNDAMENTALS_TTL)
        return result

    except Exception as e:
        logger.error(f"Failed to fetch stock info for {stock_code}: {e}")
        return {"code": stock_code, "name": stock_code, "market": "未知"}


async def get_index_data() -> list[dict]:
    """Get major index data (上证, 深证, 创业板)."""
    cached = await cache_get("indices:major")
    if cached:
        return json.loads(cached)

    try:
        df = ak.stock_zh_index_spot_em()

        if df is None or df.empty:
            return []

        # Filter for major indices
        major_codes = ["000001", "399001", "399006"]
        name_map = {"000001": "上证指数", "399001": "深证成指", "399006": "创业板指"}

        indices = []
        for code in major_codes:
            row = df[df["代码"] == code]
            if not row.empty:
                r = row.iloc[0]
                indices.append({
                    "code": code,
                    "name": name_map.get(code, str(r.get("名称", ""))),
                    "price": float(r.get("最新价", 0)),
                    "change": float(r.get("涨跌额", 0)),
                    "change_pct": float(r.get("涨跌幅", 0)),
                })

        await cache_set("indices:major", json.dumps(indices), INDEX_TTL)
        return indices

    except Exception as e:
        logger.error(f"Failed to fetch index data: {e}")
        return []


@celery_app.task(name="app.services.market_data_service.poll_market_data")
def poll_market_data():
    """Periodic task: poll real-time market data from AKShare.

    This runs every 3 seconds as a fallback for WebSocket connections.
    """
    logger.debug("Polling market data...")
    # In production, this would poll AKShare for a set of actively watched stocks
    # and update the Redis cache.
    return {"polled": True}


def _safe_float(value) -> Optional[float]:
    try:
        if value:
            return float(value)
    except (ValueError, TypeError):
        pass
    return None


def _safe_int(value) -> Optional[int]:
    try:
        if value:
            return int(float(value))
    except (ValueError, TypeError):
        pass
    return None
