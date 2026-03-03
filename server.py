import os
import json
import asyncio
import logging
import httpx
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Hyperliquid",
    instructions="Real-time market data from the Hyperliquid decentralized exchange."
)

HL_API = "https://api.hyperliquid.xyz/info"

async def hl_post(payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(HL_API, json=payload)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_all_mids() -> str:
    """Get current mid prices for ALL coins on Hyperliquid. Returns coin to mid price mapping."""
    data = await hl_post({"type": "allMids"})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_l2_book(coin: str, n_sig_figs: int = 5) -> str:
    """Get the L2 order book for a specific coin showing bid and ask levels with sizes.

    Args:
        coin: Token symbol e.g. BTC, ETH, SOL
        n_sig_figs: Number of significant figures for price levels (default 5)
    """
    data = await hl_post({
        "type": "l2Book",
        "coin": coin.upper(),
        "nSigFigs": n_sig_figs
    })
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_candle_snapshot(coin: str, interval: str, start_time: int, end_time: int = 0) -> str:
    """Get historical candlestick OHLCV data for a coin.

    Args:
        coin: Token symbol e.g. BTC, ETH, SOL
        interval: Time interval. Options: 1m, 5m, 15m, 1h, 4h, 1d
        start_time: Start time in milliseconds since epoch
        end_time: End time in milliseconds since epoch (0 means now)
    """
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": coin.upper(),
            "interval": interval,
            "startTime": start_time,
        }
    }
    if end_time > 0:
        payload["req"]["endTime"] = end_time
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_meta() -> str:
    """Get metadata for all perpetual trading pairs including max leverage, tick sizes, and asset indices."""
    data = await hl_post({"type": "meta"})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_meta_and_asset_ctxs() -> str:
    """Get metadata AND current context for all perp assets including funding rates, open interest, mark price, oracle price, and 24h volume."""
    data = await hl_post({"type": "metaAndAssetCtxs"})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_funding_history(coin: str, start_time: int, end_time: int = 0) -> str:
    """Get historical funding rate data for a coin.

    Args:
        coin: Token symbol e.g. BTC
        start_time: Start time in milliseconds since epoch
        end_time: End time in milliseconds since epoch (0 means now)
    """
    payload = {
        "type": "fundingHistory",
        "coin": coin.upper(),
        "startTime": start_time,
    }
    if end_time > 0:
        payload["endTime"] = end_time
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_recent_trades(coin: str) -> str:
    """Get the most recent trades for a specific coin.

    Args:
        coin: Token symbol e.g. BTC, ETH
    """
    data = await hl_post({
        "type": "recentTrades",
        "coin": coin.upper()
    })
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_state(user_address: str) -> str:
    """Get a user's current positions, margin info, and account value on Hyperliquid perps.

    Args:
        user_address: Ethereum wallet address starting with 0x
    """
    data = await hl_post({
        "type": "clearinghouseState",
        "user": user_address
    })
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_open_orders(user_address: str) -> str:
    """Get all open orders for a specific user address.

    Args:
        user_address: Ethereum wallet address starting with 0x
    """
    data = await hl_post({
        "type": "openOrders",
        "user": user_address
    })
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_spot_meta() -> str:
    """Get metadata for all spot trading pairs on Hyperliquid."""
    data = await hl_post({"type": "spotMeta"})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_spot_meta_and_asset_ctxs() -> str:
    """Get metadata AND current context for all spot assets."""
    data = await hl_post({"type": "spotMetaAndAssetCtxs"})
    return json.dumps(data, indent=2)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting Hyperliquid MCP server on port {port}")
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port,
        )
    )
