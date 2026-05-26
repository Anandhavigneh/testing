"""
Startup Utility Script for E2E Testing.
This script must run BEFORE executing any futures E2E test cases.

Tasks:
1. Check available balance required for testing.
2. Check active/open positions and close them.
3. Check open/pending orders and cancel them.
"""

import sys
import logging
from config import Config
from clients.futures_client import FuturesClient
from clients.futures_trading_client import FuturesTradingClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("startup_cleanup")

def check_balance():
    """Check available balance required for testing."""
    logger.info("Task 1: Checking available balance...")
    try:
        client = FuturesClient()
        details = client.fetch_user_details(ctid=Config.DEFAULT_CTID, symbol="BTC/USDT")
        
        if details.get("_api_error"):
            logger.error("Failed to fetch user details. API returned an error.")
            return

        data = details.get("Data", {})
        if not isinstance(data, dict):
            logger.error(f"Unexpected Data format: {data}")
            return
            
        wallet_balance = data.get("wallet_balance", {})
        futures_wallet = wallet_balance.get("futures_wallet", {})
        spot_wallet = wallet_balance.get("spot_wallet", {})
        
        futures_balance = float(futures_wallet.get("value", 0))
        spot_balance = float(spot_wallet.get("value", 0))
        
        logger.info(f"Available Futures Balance: {futures_balance} USDT")
        logger.info(f"Available Spot Balance: {spot_balance} USDT")
        
        if futures_balance <= 0 or spot_balance <= 0:
            logger.warning("One of the balances (Futures or Spot) is zero or negative. Sufficient balance is required for tests.")
        else:
            logger.info("Sufficient futures and spot balances are available for testing.")

    except Exception as e:
        logger.error(f"Error checking balance: {e}")

def close_active_positions():
    """Check active/open positions and close them."""
    logger.info("Task 2: Checking active positions...")
    try:
        client = FuturesTradingClient()
        resp = client.get_active_positions(ctid=Config.DEFAULT_CTID)
        
        if str(resp.get("Code")) not in ["100", "200"] and resp.get("Status") != "Success":
            logger.error(f"Failed to fetch active positions: {resp}")
            return
            
        data = resp.get("Data", [])
        positions = data if isinstance(data, list) else (data.get("list", []) or data.get("positions", []))
        
        active_positions = [p for p in positions if float(p.get("qty", p.get("quantity", "0"))) != 0]
        
        if not active_positions:
            logger.info("No active positions exist. Continue...")
            return
            
        logger.info(f"Found {len(active_positions)} active position(s). Closing them via reduce-only orders...")
        
        # We need the ticker to place limit reduce_only orders
        try:
            ticker_resp = client.client.get("ticker").json()
            ticker_data = ticker_resp.get("Data", {})
        except Exception as e:
            logger.error(f"Failed to fetch ticker data: {e}")
            ticker_data = {}
            
        for pos in active_positions:
            symbol = pos.get("symbol", "UNKNOWN")
            pos_qty_str = str(pos.get("qty", pos.get("quantity", "0")))
            pos_qty = float(pos_qty_str)
            leverage = str(pos.get("leverage", "3")).replace("x", "")
            
            if pos_qty == 0:
                continue
                
            symbol_ticker = ticker_data.get(symbol, {})
            if not symbol_ticker:
                logger.error(f"No ticker data found for {symbol}. Cannot determine close price.")
                continue

            if pos_qty > 0:
                order_side = "1" # Short to close Long
                ref_price_str = str(symbol_ticker.get("top_bid", "0"))
            else:
                order_side = "0" # Long to close Short
                ref_price_str = str(symbol_ticker.get("top_ask", "0"))
                
            close_price = float(ref_price_str)
            close_qty_str = str(abs(pos_qty))
            close_amt_str = f"{abs(pos_qty) * close_price:.4f}"
            
            logger.info(f"Closing position for {symbol} using Market Order (Qty: {close_qty_str})")
            
            try:
                close_resp = client.create_order(
                    ctid=Config.DEFAULT_CTID,
                    symbol=symbol,
                    qty=close_qty_str,
                    price="0",       # Market order uses 0 price
                    amount=close_amt_str, # Required for margin check
                    order_type="0",  # Market
                    order_side=order_side,
                    leverage=leverage,
                    reduce_only="1"
                )
                if str(close_resp.get("Code")) in ["100", "200"] or close_resp.get("Status") in ["Success", "100", "200"]:
                    logger.info(f"Successfully created close order for {symbol}.")
                else:
                    logger.error(f"Failed to close position for {symbol}: {close_resp}")
            except Exception as e:
                logger.error(f"Error closing position for {symbol}: {e}")

    except Exception as e:
        logger.error(f"Error fetching/closing positions: {e}")

def cancel_open_orders():
    """Check open/pending orders and cancel them."""
    logger.info("Task 3: Checking open orders...")
    try:
        client = FuturesTradingClient()
        resp = client.get_open_orders(ctid=Config.DEFAULT_CTID)
        
        if str(resp.get("Code")) not in ["100", "200"] and resp.get("Status") != "Success":
            logger.error(f"Failed to fetch open orders: {resp}")
            return
            
        data = resp.get("Data", [])
        orders = data if isinstance(data, list) else (data.get("list", []) or data.get("orders", []))
        
        if not orders:
            logger.info("No open orders exist. Continue...")
            return
            
        logger.info(f"Found {len(orders)} open order(s). Canceling them...")
        
        for order in orders:
            order_id = order.get("order_id", order.get("id"))
            symbol = order.get("symbol", "UNKNOWN")
            
            if not order_id:
                logger.warning(f"Could not find order ID for order: {order}")
                continue
                
            try:
                payload = {
                    "ctid": Config.DEFAULT_CTID,
                    "order_id": str(order_id),
                    "client_order_id": str(order.get("client_order_id", ""))
                }
                cancel_resp = client.client.post("order/cancel", json=payload).json()
                if str(cancel_resp.get("Code")) in ["100", "200"] or cancel_resp.get("Status") in ["Success", "100", "200"]:
                    logger.info(f"Successfully canceled order for {symbol} (ID: {order_id})")
                else:
                    logger.error(f"Failed to cancel order {order_id}: {cancel_resp}")
            except Exception as e:
                logger.error(f"Error canceling order {order_id}: {e}")

    except Exception as e:
        logger.error(f"Error fetching/canceling orders: {e}")

def main():
    logger.info("Starting pre-test cleanup...")
    logger.info("-" * 40)
    
    check_balance()
    logger.info("-" * 40)
    
    cancel_open_orders()
    logger.info("-" * 40)
    
    close_active_positions()
    logger.info("-" * 40)
    
    logger.info("Cleanup summary: Pre-test cleanup finished.")

if __name__ == "__main__":
    main()
