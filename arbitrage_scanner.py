#!/usr/bin/env python3
"""
Triangular Arbitrage Scanner - Real-time Binance API
Author: zvwgvx
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════
BINANCE_API = "https://api.binance.com/api/v3"
FEE = 0.001  # 0.1% trading fee (Binance spot)
MIN_PROFIT = 0.05  # Minimum profit % to display (lowered for real opportunities)
SCAN_INTERVAL = 2  # Seconds between scans

# Coins to monitor (only liquid quote currencies and popular coins)
QUOTE_CURRENCIES = ["USDT", "BTC", "ETH"]  # Removed BUSD (delisted)
TARGET_COINS = ["BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "AVAX", "MATIC", 
                "LINK", "LTC"]  # Only top liquid coins


@dataclass
class ArbitrageOpportunity:
    triangle: Tuple[str, str, str]  # (A, B, C)
    direction: str  # "A->B->C->A" or "A->C->B->A"
    fair_price: float
    actual_price: float
    deviation: float  # percentage
    profit: float  # percentage after fees
    steps: List[str]
    timestamp: str


class BinanceAPI:
    def __init__(self):
        self.prices: Dict[str, float] = {}
        self.symbols_info: Dict[str, dict] = {}
        
    def fetch_all_prices(self) -> bool:
        """Fetch all ticker prices from Binance"""
        try:
            response = requests.get(f"{BINANCE_API}/ticker/price", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.prices = {item['symbol']: float(item['price']) for item in data}
                return True
        except Exception as e:
            print(f"Error fetching prices: {e}")
        return False
    
    def get_price(self, base: str, quote: str) -> Optional[float]:
        """Get price for a trading pair"""
        symbol = f"{base}{quote}"
        if symbol in self.prices:
            return self.prices[symbol]
        # Try reverse pair
        reverse_symbol = f"{quote}{base}"
        if reverse_symbol in self.prices:
            return 1.0 / self.prices[reverse_symbol]
        return None


class TriangularArbitrageScanner:
    def __init__(self, api: BinanceAPI):
        self.api = api
        self.opportunities: List[ArbitrageOpportunity] = []
        
    def calculate_fair_price(self, price_bq: float, price_cq: float) -> float:
        """Calculate fair price of C/B based on quote currency prices"""
        return price_cq / price_bq
    
    def calculate_profit_clockwise(self, price_bq: float, price_cq: float, price_cb: float) -> float:
        """Q -> B -> C -> Q (use when C/B is underpriced)"""
        step1 = (1.0 / price_bq) * (1 - FEE)  # Q -> B
        step2 = (step1 / price_cb) * (1 - FEE)  # B -> C
        step3 = (step2 * price_cq) * (1 - FEE)  # C -> Q
        return (step3 - 1.0) * 100
    
    def calculate_profit_counterclockwise(self, price_bq: float, price_cq: float, price_cb: float) -> float:
        """Q -> C -> B -> Q (use when C/B is overpriced)"""
        step1 = (1.0 / price_cq) * (1 - FEE)  # Q -> C
        step2 = (step1 * price_cb) * (1 - FEE)  # C -> B
        step3 = (step2 * price_bq) * (1 - FEE)  # B -> Q
        return (step3 - 1.0) * 100
    
    def scan_triangle(self, quote: str, coin_b: str, coin_c: str) -> Optional[ArbitrageOpportunity]:
        """Scan a single triangle for arbitrage opportunity"""
        # Get prices
        price_bq = self.api.get_price(coin_b, quote)  # B/Q (e.g., BTC/USDT)
        price_cq = self.api.get_price(coin_c, quote)  # C/Q (e.g., ETH/USDT)
        price_cb = self.api.get_price(coin_c, coin_b)  # C/B (e.g., ETH/BTC)
        
        if not all([price_bq, price_cq, price_cb]):
            return None
        
        # Calculate fair price and deviation
        fair_price = self.calculate_fair_price(price_bq, price_cq)
        deviation = ((price_cb - fair_price) / fair_price) * 100
        
        # Calculate profits both ways
        profit_cw = self.calculate_profit_clockwise(price_bq, price_cq, price_cb)
        profit_ccw = self.calculate_profit_counterclockwise(price_bq, price_cq, price_cb)
        
        # Choose better direction
        if profit_cw > profit_ccw and profit_cw > 0:
            return ArbitrageOpportunity(
                triangle=(quote, coin_b, coin_c),
                direction=f"{quote} → {coin_b} → {coin_c} → {quote}",
                fair_price=fair_price,
                actual_price=price_cb,
                deviation=deviation,
                profit=profit_cw,
                steps=[
                    f"1. Buy {coin_b} with {quote} @ {price_bq:.8f}",
                    f"2. Buy {coin_c} with {coin_b} @ {price_cb:.8f} (ARBITRAGE)",
                    f"3. Sell {coin_c} for {quote} @ {price_cq:.8f}"
                ],
                timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3]
            )
        elif profit_ccw > 0:
            return ArbitrageOpportunity(
                triangle=(quote, coin_b, coin_c),
                direction=f"{quote} → {coin_c} → {coin_b} → {quote}",
                fair_price=fair_price,
                actual_price=price_cb,
                deviation=deviation,
                profit=profit_ccw,
                steps=[
                    f"1. Buy {coin_c} with {quote} @ {price_cq:.8f}",
                    f"2. Sell {coin_c} for {coin_b} @ {price_cb:.8f} (ARBITRAGE)",
                    f"3. Sell {coin_b} for {quote} @ {price_bq:.8f}"
                ],
                timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3]
            )
        
        return None
    
    def scan_all_triangles(self) -> List[ArbitrageOpportunity]:
        """Scan all possible triangles"""
        opportunities = []
        
        for quote in QUOTE_CURRENCIES:
            coins = [c for c in TARGET_COINS if c != quote]
            
            for i, coin_b in enumerate(coins):
                for coin_c in coins[i+1:]:
                    opp = self.scan_triangle(quote, coin_b, coin_c)
                    if opp and opp.profit >= MIN_PROFIT:
                        opportunities.append(opp)
        
        # Sort by profit descending
        opportunities.sort(key=lambda x: x.profit, reverse=True)
        return opportunities


def print_header():
    print("\033[2J\033[H")  # Clear screen
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║         TRIANGULAR ARBITRAGE SCANNER - BINANCE REALTIME             ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(f"  Fee: {FEE*100:.2f}% | Min Profit: {MIN_PROFIT}% | Scan Interval: {SCAN_INTERVAL}s")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("─" * 74)


def print_opportunities(opportunities: List[ArbitrageOpportunity]):
    if not opportunities:
        print("\n  [!] No profitable opportunities found at this moment.")
        print("      Market is efficient - keep scanning!")
        return
    
    print(f"\n  Found {len(opportunities)} profitable opportunities:\n")
    print(f"  {'#':<3} {'Triangle':<25} {'Deviation':<12} {'Profit':<10} {'Direction'}")
    print("  " + "─" * 70)
    
    for i, opp in enumerate(opportunities[:15], 1):  # Show top 15
        triangle_str = f"{opp.triangle[0]}-{opp.triangle[1]}-{opp.triangle[2]}"
        dev_str = f"{opp.deviation:+.3f}%"
        profit_str = f"{opp.profit:.4f}%"
        
        # Color coding
        if opp.profit >= 1.0:
            color = "\033[92m"  # Green
        elif opp.profit >= 0.5:
            color = "\033[93m"  # Yellow
        else:
            color = "\033[0m"  # Normal
        
        print(f"  {color}{i:<3} {triangle_str:<25} {dev_str:<12} {profit_str:<10} {opp.direction}\033[0m")
    
    if len(opportunities) > 15:
        print(f"\n  ... and {len(opportunities) - 15} more opportunities")


def print_best_opportunity(opp: ArbitrageOpportunity, capital: float = 1000):
    if not opp:
        return
    
    print("\n" + "═" * 74)
    print("  BEST OPPORTUNITY DETAILS:")
    print("═" * 74)
    
    print(f"\n  Triangle: {opp.triangle[0]} - {opp.triangle[1]} - {opp.triangle[2]}")
    print(f"  Direction: {opp.direction}")
    print(f"  Fair Price ({opp.triangle[2]}/{opp.triangle[1]}): {opp.fair_price:.8f}")
    print(f"  Actual Price: {opp.actual_price:.8f}")
    print(f"  Deviation: {opp.deviation:+.4f}%")
    print(f"  Estimated Profit: {opp.profit:.4f}%")
    
    print(f"\n  Trade Steps:")
    for step in opp.steps:
        print(f"     {step}")
    
    # Simulate trade
    estimated_return = capital * (1 + opp.profit / 100)
    print(f"\n  With ${capital:.2f} capital:")
    print(f"     Expected return: ${estimated_return:.2f}")
    print(f"     Profit: ${estimated_return - capital:.2f}")


def main():
    print("Initializing Binance API connection...")
    
    api = BinanceAPI()
    scanner = TriangularArbitrageScanner(api)
    
    scan_count = 0
    total_opportunities = 0
    best_profit_ever = 0
    
    try:
        while True:
            scan_count += 1
            
            # Fetch latest prices
            if not api.fetch_all_prices():
                print("Failed to fetch prices. Retrying...")
                time.sleep(1)
                continue
            
            # Scan for opportunities
            opportunities = scanner.scan_all_triangles()
            total_opportunities += len(opportunities)
            
            # Update best ever
            if opportunities and opportunities[0].profit > best_profit_ever:
                best_profit_ever = opportunities[0].profit
            
            # Display results
            print_header()
            print(f"  Scan #{scan_count} | Total pairs: {len(api.prices)} | Best ever: {best_profit_ever:.4f}%")
            print_opportunities(opportunities)
            
            if opportunities:
                print_best_opportunity(opportunities[0])
            
            print(f"\n  Press Ctrl+C to stop. Next scan in {SCAN_INTERVAL}s...")
            time.sleep(SCAN_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n" + "═" * 74)
        print("  SESSION SUMMARY")
        print("═" * 74)
        print(f"  Total scans: {scan_count}")
        print(f"  Total opportunities found: {total_opportunities}")
        print(f"  Best profit seen: {best_profit_ever:.4f}%")
        print("  Goodbye!")


if __name__ == "__main__":
    main()
