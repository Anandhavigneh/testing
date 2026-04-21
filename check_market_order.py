import json
from config import Config
from clients.futures_trading_client import FuturesTradingClient

def test_btc_market_order():
    print(f"Testing Market Order for CTID: {Config.DEFAULT_CTID}")
    

    client = FuturesTradingClient()
    
    payload = {
        "ctid": Config.DEFAULT_CTID,
        "symbol": "BTC/USDT",
        "qty": "0.002",       
        "price": "76250",          
        "amount": "152.4804",
        "order_type": "1",     
        "order_side": "0",     
        "leverage": "3",       
        "reduce_only": "0"     
    }
    
    print("\nSending Payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = client.create_order(**payload)
        print("\nAPI Response:")
        print(json.dumps(response, indent=2))
        
        if response.get("Status") == "Success":
            print("\n✅ SUCCESS: Order placed successfully!")
        else:
            print("\n❌ FAILED: API rejected the order.")
            
    except Exception as e:
        print(f"\n❌ CRASH: Network or Code error: {e}")

if __name__ == "__main__":
    test_btc_market_order()
