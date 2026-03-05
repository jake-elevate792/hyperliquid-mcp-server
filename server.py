import os
import json
import asyncio
import logging
import httpx
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Hyperliquid",
    instructions="Real-time market data, account state, and analytics from the Hyperliquid decentralized exchange. Covers perp and spot markets, user positions, fills, funding, vaults, staking, and borrow/lend."
)

HL_API = "https://api.hyperliquid.xyz/info"


async def hl_post(payload: dict) -> dict:
    """Make a POST request to the Hyperliquid info API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(HL_API, json=payload)
        resp.raise_for_status()
        return resp.json()


# ═══════════════════════════════════════════════════════════════
# MARKET DATA — prices, order books, candles, trades
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def get_all_mids(dex: str = "") -> str:
    """Get current mid prices for ALL coins on Hyperliquid.

    Args:
        dex: Perp dex name. Empty string (default) = first perp dex. Spot mids only included with first perp dex.
    """
    payload = {"type": "allMids"}
    if dex:
        payload["dex"] = dex
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_l2_book(coin: str, n_sig_figs: int = 5, mantissa: int = 0) -> str:
    """Get the L2 order book for a specific coin. Returns up to 20 levels per side.

    Args:
        coin: Token symbol, e.g. 'BTC', 'ETH', 'SOL'
        n_sig_figs: Significant figures for price aggregation (2-5). Default 5 = full precision.
        mantissa: Only allowed when n_sig_figs=5. Accepts 1, 2, or 5. Set 0 to omit.
    """
    payload = {"type": "l2Book", "coin": coin.upper(), "nSigFigs": n_sig_figs}
    if mantissa and n_sig_figs == 5:
        payload["mantissa"] = mantissa
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_candle_snapshot(coin: str, interval: str, start_time: int, end_time: int = 0) -> str:
    """Get historical candlestick (OHLCV) data. Max 5000 candles per request.

    Args:
        coin: Token symbol, e.g. 'BTC'. For HIP-3 prefix with dex name e.g. 'xyz:XYZ100'.
        interval: One of: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 8h, 12h, 1d, 3d, 1w, 1M
        start_time: Start time in milliseconds since epoch
        end_time: End time in milliseconds since epoch (0 = now)
    """
    payload = {
        "type": "candleSnapshot",
        "req": {"coin": coin, "interval": interval, "startTime": start_time}
    }
    if end_time > 0:
        payload["req"]["endTime"] = end_time
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_recent_trades(coin: str) -> str:
    """Get the most recent trades for a specific coin.

    Args:
        coin: Token symbol, e.g. 'BTC', 'ETH'
    """
    data = await hl_post({"type": "recentTrades", "coin": coin.upper()})
    return json.dumps(data, indent=2)


# ═══════════════════════════════════════════════════════════════
# PERPETUALS — metadata, asset contexts, funding, OI
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def get_meta(dex: str = "") -> str:
    """Get perpetuals metadata: universe of all perp assets with name, szDecimals, maxLeverage, and margin tables.

    Args:
        dex: Perp dex name. Empty string = first perp dex.
    """
    payload = {"type": "meta"}
    if dex:
        payload["dex"] = dex
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_meta_and_asset_ctxs(dex: str = "") -> str:
    """Get metadata AND live context for all perp assets: mark price, mid price, oracle price, funding rate, open interest, 24h volume, premium, impact prices.

    Args:
        dex: Perp dex name. Empty string = first perp dex.
    """
    payload = {"type": "metaAndAssetCtxs"}
    if dex:
        payload["dex"] = dex
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_funding_history(coin: str, start_time: int, end_time: int = 0) -> str:
    """Get historical funding rates and premiums for a coin. Max 500 records per request — paginate using last timestamp.

    Args:
        coin: Token symbol, e.g. 'BTC'. For HIP-3: 'xyz:XYZ100'.
        start_time: Start time in milliseconds since epoch
        end_time: End time in milliseconds since epoch (0 = now)
    """
    payload = {"type": "fundingHistory", "coin": coin, "startTime": start_time}
    if end_time > 0:
        payload["endTime"] = end_time
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_predicted_fundings() -> str:
    """Get predicted funding rates across exchanges (Binance, Bybit, Hyperliquid) for all coins. Includes next funding time for each venue. Only supported for the first perp dex."""
    data = await hl_post({"type": "predictedFundings"})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_perps_at_oi_cap(dex: str = "") -> str:
    """Get list of perps that have hit their open interest caps.

    Args:
        dex: Perp dex name. Empty string = first perp dex.
    """
    payload = {"type": "perpsAtOpenInterestCap"}
    if dex:
        payload["dex"] = dex
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_perp_dexs() -> str:
    """Get list of all perpetual dexs (first perp dex + all builder-deployed HIP-3 dexs) with deployer, oracle updater, fee recipient, OI caps, funding multipliers."""
    data = await hl_post({"type": "perpDexs"})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_all_perp_metas() -> str:
    """Get metadata (universe + margin tables) for ALL perp dexs at once."""
    data = await hl_post({"type": "allPerpMetas"})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_perp_annotation(coin: str) -> str:
    """Get category and description for a specific perp.

    Args:
        coin: Coin name, e.g. 'BTC'
    """
    data = await hl_post({"type": "perpAnnotation", "coin": coin})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_perp_categories() -> str:
    """Get category tags for all perps (e.g. ai, preipo, etc.)."""
    data = await hl_post({"type": "perpCategories"})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_perp_deploy_auction_status() -> str:
    """Get current state of the perp deploy auction: start time, duration, start/current/end gas."""
    data = await hl_post({"type": "perpDeployAuctionStatus"})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_perp_dex_limits(dex: str) -> str:
    """Get OI caps and transfer limits for a builder-deployed perp dex.

    Args:
        dex: Perp dex name (required, cannot be empty string).
    """
    data = await hl_post({"type": "perpDexLimits", "dex": dex})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_perp_dex_status(dex: str = "") -> str:
    """Get total net deposits for a perp dex.

    Args:
        dex: Perp dex name. Empty string = first perp dex.
    """
    data = await hl_post({"type": "perpDexStatus", "dex": dex})
    return json.dumps(data, indent=2)


# ═══════════════════════════════════════════════════════════════
# SPOT — metadata and context
# ═══════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════
# USER ACCOUNT — positions, margin, orders, fills
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def get_user_state(user_address: str, dex: str = "") -> str:
    """Get a user's perp account summary: open positions (entry price, liquidation price, unrealized PnL, leverage, cumulative funding), margin summary, account value, withdrawable balance.

    Args:
        user_address: Ethereum wallet address (0x...)
        dex: Perp dex name. Empty string = first perp dex.
    """
    payload = {"type": "clearinghouseState", "user": user_address}
    if dex:
        payload["dex"] = dex
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_open_orders(user_address: str, dex: str = "") -> str:
    """Get all open orders for a user: coin, side, price, size, oid, timestamp.

    Args:
        user_address: Ethereum wallet address (0x...)
        dex: Perp dex name. Empty string = first perp dex.
    """
    payload = {"type": "openOrders", "user": user_address}
    if dex:
        payload["dex"] = dex
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_frontend_open_orders(user_address: str, dex: str = "") -> str:
    """Get open orders with additional detail: order type (Limit/Market/Stop), original size, trigger conditions, trigger price, reduce-only flag, TP/SL status, children orders.

    Args:
        user_address: Ethereum wallet address (0x...)
        dex: Perp dex name. Empty string = first perp dex.
    """
    payload = {"type": "frontendOpenOrders", "user": user_address}
    if dex:
        payload["dex"] = dex
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_fills(user_address: str, aggregate_by_time: bool = False) -> str:
    """Get a user's most recent 2000 fills across all coins. Includes price, size, side, direction, closed PnL, fees.

    Args:
        user_address: Ethereum wallet address (0x...)
        aggregate_by_time: When true, partial fills from same crossing order are combined.
    """
    payload = {"type": "userFills", "user": user_address}
    if aggregate_by_time:
        payload["aggregateByTime"] = True
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_fills_by_time(user_address: str, start_time: int, end_time: int = 0, aggregate_by_time: bool = False) -> str:
    """Get a user's fills filtered by time range. Max 2000 per response, 10000 most recent available.

    Args:
        user_address: Ethereum wallet address (0x...)
        start_time: Start time in milliseconds since epoch
        end_time: End time in milliseconds since epoch (0 = now)
        aggregate_by_time: When true, partial fills from same crossing order are combined.
    """
    payload = {"type": "userFillsByTime", "user": user_address, "startTime": start_time}
    if end_time > 0:
        payload["endTime"] = end_time
    if aggregate_by_time:
        payload["aggregateByTime"] = True
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_funding(user_address: str, start_time: int, end_time: int = 0) -> str:
    """Get a user's funding payment history: coin, funding rate, position size, USDC amount per payment.

    Args:
        user_address: Ethereum wallet address (0x...)
        start_time: Start time in milliseconds since epoch
        end_time: End time in milliseconds since epoch (0 = now)
    """
    payload = {"type": "userFunding", "user": user_address, "startTime": start_time}
    if end_time > 0:
        payload["endTime"] = end_time
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_non_funding_ledger(user_address: str, start_time: int, end_time: int = 0) -> str:
    """Get a user's non-funding ledger updates: deposits, withdrawals, transfers, liquidations.

    Args:
        user_address: Ethereum wallet address (0x...)
        start_time: Start time in milliseconds since epoch
        end_time: End time in milliseconds since epoch (0 = now)
    """
    payload = {"type": "userNonFundingLedgerUpdates", "user": user_address, "startTime": start_time}
    if end_time > 0:
        payload["endTime"] = end_time
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_historical_orders(user_address: str) -> str:
    """Get a user's most recent 2000 historical orders with full status: filled, canceled, triggered, rejected, marginCanceled, liquidatedCanceled, etc.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "historicalOrders", "user": user_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_order_status(user_address: str, oid: str) -> str:
    """Get status of a specific order by oid or cloid.

    Args:
        user_address: Ethereum wallet address (0x...)
        oid: Order ID (numeric string) or client order ID (16-byte hex string)
    """
    # Try to parse as int for numeric oid, otherwise pass as cloid string
    try:
        oid_val = int(oid)
    except ValueError:
        oid_val = oid
    data = await hl_post({"type": "orderStatus", "user": user_address, "oid": oid_val})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_twap_slice_fills(user_address: str) -> str:
    """Get a user's most recent 2000 TWAP execution slice fills with twapId.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "userTwapSliceFills", "user": user_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_active_asset_data(user_address: str, coin: str) -> str:
    """Get a user's active asset data for a specific coin: current leverage, max trade sizes (long/short), available margin to trade, mark price.

    Args:
        user_address: Ethereum wallet address (0x...)
        coin: Coin symbol, e.g. 'BTC'. For HIP-3: 'xyz:XYZ100'.
    """
    data = await hl_post({"type": "activeAssetData", "user": user_address, "coin": coin})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_rate_limit(user_address: str) -> str:
    """Get a user's API rate limit status: cumulative volume, requests used vs cap, surplus.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "userRateLimit", "user": user_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_fees(user_address: str) -> str:
    """Get a user's fee schedule: VIP/MM tiers, daily volume, effective cross/add rates, spot rates, staking discount, referral discount.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "userFees", "user": user_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_portfolio(user_address: str) -> str:
    """Get a user's portfolio: account value history and PnL history across timeframes (day, week, month, allTime, perpDay, perpWeek, perpMonth, perpAllTime), plus volume.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "portfolio", "user": user_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_sub_accounts(user_address: str) -> str:
    """Get all subaccounts for a user with name, address, master, full clearinghouse state, and spot balances.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "subAccounts", "user": user_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_role(user_address: str) -> str:
    """Get a user's role: user, agent, vault, subAccount, or missing.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "userRole", "user": user_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_referral(user_address: str) -> str:
    """Get a user's referral info: referred by, cumulative volume, unclaimed/claimed rewards, builder rewards, referrer state with referred users.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "referral", "user": user_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_max_builder_fee(user_address: str, builder_address: str) -> str:
    """Check builder fee approval: max fee approved for a builder address (in tenths of a basis point).

    Args:
        user_address: Ethereum wallet address (0x...)
        builder_address: Builder address (0x...)
    """
    data = await hl_post({"type": "maxBuilderFee", "user": user_address, "builder": builder_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_abstraction(user_address: str) -> str:
    """Get a user's abstraction state: unifiedAccount, portfolioMargin, disabled, default, or dexAbstraction.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "userAbstraction", "user": user_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_dex_abstraction(user_address: str) -> str:
    """Get a user's HIP-3 dex abstraction state (true/false).

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "userDexAbstraction", "user": user_address})
    return json.dumps(data, indent=2)


# ═══════════════════════════════════════════════════════════════
# VAULTS
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def get_vault_details(vault_address: str, user_address: str = "") -> str:
    """Get vault details: portfolio history (account value, PnL, volume) across timeframes, APR, followers, leader commission, max distributable/withdrawable.

    Args:
        vault_address: Vault address (0x...)
        user_address: Optional user address to include follower-specific data.
    """
    payload = {"type": "vaultDetails", "vaultAddress": vault_address}
    if user_address:
        payload["user"] = user_address
    data = await hl_post(payload)
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_user_vault_equities(user_address: str) -> str:
    """Get a user's equity in all vaults they've deposited into.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "userVaultEquities", "user": user_address})
    return json.dumps(data, indent=2)


# ═══════════════════════════════════════════════════════════════
# STAKING
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def get_delegations(user_address: str) -> str:
    """Get a user's staking delegations: validator addresses, amounts, lockedUntilTimestamp.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "delegations", "user": user_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_delegator_summary(user_address: str) -> str:
    """Get a user's staking summary: total delegated, undelegated, pending withdrawals count and amount.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "delegatorSummary", "user": user_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_delegator_history(user_address: str) -> str:
    """Get a user's staking history: delegation/undelegation events with timestamps, hashes, validator addresses, amounts.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "delegatorHistory", "user": user_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_delegator_rewards(user_address: str) -> str:
    """Get a user's staking rewards: history with source (delegation vs commission), amounts, timestamps.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "delegatorRewards", "user": user_address})
    return json.dumps(data, indent=2)


# ═══════════════════════════════════════════════════════════════
# BORROW / LEND
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def get_borrow_lend_user_state(user_address: str) -> str:
    """Get a user's borrow/lend positions: per-token borrow and supply with basis and current value, health status, health factor.

    Args:
        user_address: Ethereum wallet address (0x...)
    """
    data = await hl_post({"type": "borrowLendUserState", "user": user_address})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_borrow_lend_reserve_state(token: int) -> str:
    """Get borrow/lend reserve state for a specific token: borrow/supply yearly rates, utilization, balance, oracle price, LTV, total supplied/borrowed.

    Args:
        token: Token index (e.g. 0 for USDC, 150 for HYPE).
    """
    data = await hl_post({"type": "borrowLendReserveState", "token": token})
    return json.dumps(data, indent=2)


@mcp.tool()
async def get_all_borrow_lend_reserve_states() -> str:
    """Get borrow/lend reserve state for ALL tokens at once: rates, utilization, balances, LTVs."""
    data = await hl_post({"type": "allBorrowLendReserveStates"})
    return json.dumps(data, indent=2)


# ═══════════════════════════════════════════════════════════════
# MISC
# ═══════════════════════════════════════════════════════════════

@mcp.tool()
async def get_aligned_quote_token_info(token: int) -> str:
    """Get aligned quote token status: alignment status, first aligned time, EVM minted supply, daily amount owed, predicted rate.

    Args:
        token: Token index.
    """
    data = await hl_post({"type": "alignedQuoteTokenInfo", "token": token})
    return json.dumps(data, indent=2)


# ═══════════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════════

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
