#!/usr/bin/env python3
"""Quick test - Single scan"""
import requests
from datetime import datetime

BINANCE_API = "https://api.binance.com/api/v3"
FEE = 0.001

def main():
    print("Fetching prices from Binance...")
    
    # Fetch prices
    resp = requests.get(f"{BINANCE_API}/ticker/price", timeout=10)
    prices = {item['symbol']: float(item['price']) for item in resp.json()}
    
    print(f"✓ Fetched {len(prices)} trading pairs\n")
    
    # Test triangles
    triangles = [
        ("USDT", "BTC", "ETH"),
        ("USDT", "BTC", "BNB"),
        ("USDT", "BTC", "SOL"),
        ("USDT", "ETH", "BNB"),
        ("USDT", "ETH", "SOL"),
        ("BTC", "ETH", "BNB"),
    ]
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║         TRIANGULAR ARBITRAGE - BINANCE LIVE DATA            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    
    for quote, coin_b, coin_c in triangles:
        # Get prices
        sym_bq = f"{coin_b}{quote}"
        sym_cq = f"{coin_c}{quote}"
        sym_cb = f"{coin_c}{coin_b}"
        
        if sym_bq not in prices or sym_cq not in prices or sym_cb not in prices:
            continue
            
        price_bq = prices[sym_bq]
        price_cq = prices[sym_cq]
        price_cb = prices[sym_cb]
        
        # Fair price
        fair_price = price_cq / price_bq
        deviation = ((price_cb - fair_price) / fair_price) * 100
        
        # Clockwise: Q -> B -> C -> Q
        step1 = (1.0 / price_bq) * (1 - FEE)
        step2 = (step1 / price_cb) * (1 - FEE)
        step3 = (step2 * price_cq) * (1 - FEE)
        profit_cw = (step3 - 1.0) * 100
        
        # Counter-clockwise: Q -> C -> B -> Q
        step1 = (1.0 / price_cq) * (1 - FEE)
        step2 = (step1 * price_cb) * (1 - FEE)
        step3 = (step2 * price_bq) * (1 - FEE)
        profit_ccw = (step3 - 1.0) * 100
        
        best_profit = max(profit_cw, profit_ccw)
        direction = "CW" if profit_cw > profit_ccw else "CCW"
        
        results.append({
            'triangle': f"{quote}-{coin_b}-{coin_c}",
            'fair': fair_price,
            'actual': price_cb,
            'deviation': deviation,
            'profit': best_profit,
            'direction': direction,
            'prices': (price_bq, price_cq, price_cb)
        })
    
    # Sort by profit
    results.sort(key=lambda x: x['profit'], reverse=True)
    
    print(f"{'Triangle':<18} {'Fair Price':<14} {'Actual':<14} {'Deviation':<12} {'Profit'}")
    print("─" * 70)
    
    for r in results:
        color = "\033[92m" if r['profit'] > 0 else "\033[91m"
        print(f"{color}{r['triangle']:<18} {r['fair']:<14.8f} {r['actual']:<14.8f} {r['deviation']:+.4f}%     {r['profit']:.4f}%\033[0m")
    
    # Best opportunity details
    if results and results[0]['profit'] > 0:
        best = results[0]
        print(f"\n{'═'*70}")
        print("🏆 BEST OPPORTUNITY:")
        print(f"   Triangle: {best['triangle']}")
        print(f"   Direction: {'Clockwise' if best['direction'] == 'CW' else 'Counter-clockwise'}")
        print(f"   Deviation from fair price: {best['deviation']:+.4f}%")
        print(f"   Expected profit: {best['profit']:.4f}%")
        
        # Simulate with $10,000
        capital = 10000
        final = capital * (1 + best['profit']/100)
        print(f"\n   💰 With ${capital:,.0f} capital:")
        print(f"      Return: ${final:,.2f}")
        print(f"      Profit: ${final - capital:,.2f}")
    else:
        print("\n⚠️  No profitable arbitrage at this moment (market is efficient)")


if __name__ == "__main__":
    main()
