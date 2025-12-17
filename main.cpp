#include <bits/stdc++.h>

using namespace std;

constexpr double FEE = 0.001;  // 0.1% trading fee

struct TriangularArbitrage {
    string coinA, coinB, coinC;
    double priceAB;      // A/B (e.g., BTC/USDT = 50000)
    double priceAC;      // A/C (e.g., ETH/USDT = 3000)
    double priceCB_real; // C/B actual (e.g., ETH/BTC = 0.055)
    double priceCB_fair; // C/B fair = priceAC / priceAB
    double deviation;    // % deviation from fair price
    double profit;       // profit percentage
    string direction;    // "clockwise" or "counter-clockwise"
};

class ArbitrageDetector {
public:
    TriangularArbitrage detectOpportunity(
        const string& baseQuote,    // e.g., "USDT"
        const string& coinB,        // e.g., "BTC"  
        const string& coinC,        // e.g., "ETH"
        double priceBQ,             // BTC/USDT = 50000
        double priceCQ,             // ETH/USDT = 3000
        double priceCB              // ETH/BTC = 0.055 (actual market price)
    ) {
        TriangularArbitrage arb;
        arb.coinA = baseQuote;
        arb.coinB = coinB;
        arb.coinC = coinC;
        arb.priceAB = priceBQ;
        arb.priceAC = priceCQ;
        arb.priceCB_real = priceCB;
        
        // Fair price formula: ETH/BTC = ETH/USDT ÷ BTC/USDT
        arb.priceCB_fair = priceCQ / priceBQ;
        
        // Deviation percentage
        arb.deviation = ((arb.priceCB_real - arb.priceCB_fair) / arb.priceCB_fair) * 100;
        
        // Calculate profit for both directions
        double profitCW = calcProfit_Clockwise(priceBQ, priceCQ, priceCB);
        double profitCCW = calcProfit_CounterClockwise(priceBQ, priceCQ, priceCB);
        
        if (profitCW > profitCCW) {
            arb.profit = profitCW;
            arb.direction = "USDT -> BTC -> ETH -> USDT";
        } else {
            arb.profit = profitCCW;
            arb.direction = "USDT -> ETH -> BTC -> USDT";
        }
        
        return arb;
    }
    
    // Direction 1: USDT -> BTC -> ETH -> USDT
    // Use when ETH/BTC is LOWER than fair (ETH is cheap in BTC terms)
    double calcProfit_Clockwise(double priceBQ, double priceCQ, double priceCB) {
        double step1 = (1.0 / priceBQ) * (1 - FEE);       // USDT -> BTC
        double step2 = (step1 / priceCB) * (1 - FEE);     // BTC -> ETH
        double step3 = (step2 * priceCQ) * (1 - FEE);     // ETH -> USDT
        return (step3 - 1.0) * 100;
    }
    
    // Direction 2: USDT -> ETH -> BTC -> USDT  
    // Use when ETH/BTC is HIGHER than fair (ETH is expensive in BTC terms)
    double calcProfit_CounterClockwise(double priceBQ, double priceCQ, double priceCB) {
        double step1 = (1.0 / priceCQ) * (1 - FEE);       // USDT -> ETH
        double step2 = (step1 * priceCB) * (1 - FEE);     // ETH -> BTC
        double step3 = (step2 * priceBQ) * (1 - FEE);     // BTC -> USDT
        return (step3 - 1.0) * 100;
    }
    
    void simulateTrade(const TriangularArbitrage& arb, double capital) {
        cout << "\n╔══════════════════════════════════════════════════════════════╗\n";
        cout << "║              TRIANGULAR ARBITRAGE SIMULATION                 ║\n";
        cout << "╚══════════════════════════════════════════════════════════════╝\n\n";
        
        cout << "Market Prices:\n";
        cout << "  " << arb.coinB << "/" << arb.coinA << " = $" << fixed << setprecision(2) << arb.priceAB << "\n";
        cout << "  " << arb.coinC << "/" << arb.coinA << " = $" << arb.priceAC << "\n";
        cout << "  " << arb.coinC << "/" << arb.coinB << " = " << setprecision(6) << arb.priceCB_real << "\n\n";
        
        cout << "Fair Price Analysis:\n";
        cout << "  Fair " << arb.coinC << "/" << arb.coinB << " = " << arb.priceAC << " / " << arb.priceAB 
             << " = " << setprecision(6) << arb.priceCB_fair << "\n";
        cout << "  Actual " << arb.coinC << "/" << arb.coinB << " = " << arb.priceCB_real << "\n";
        cout << "  Deviation: " << setprecision(2) << arb.deviation << "%";
        
        if (arb.deviation < 0) {
            cout << " (ETH is CHEAP when buying with BTC)\n";
        } else {
            cout << " (ETH is EXPENSIVE when buying with BTC)\n";
        }
        
        cout << "\n─────────────────────────────────────────────────────\n";
        cout << "Trade Execution: " << arb.direction << "\n";
        cout << "Starting Capital: " << setprecision(2) << capital << " " << arb.coinA << "\n";
        cout << "─────────────────────────────────────────────────────\n\n";
        
        if (arb.direction.find("BTC -> ETH") != string::npos) {
            // Clockwise: USDT -> BTC -> ETH -> USDT
            double btc = (capital / arb.priceAB) * (1 - FEE);
            cout << "Step 1: Buy " << arb.coinB << " with " << arb.coinA << "\n";
            cout << "        " << capital << " " << arb.coinA << " / $" << arb.priceAB 
                 << " × (1-" << FEE*100 << "%) = " << setprecision(6) << btc << " " << arb.coinB << "\n\n";
            
            double eth = (btc / arb.priceCB_real) * (1 - FEE);
            cout << "Step 2: Buy " << arb.coinC << " with " << arb.coinB << " (ARBITRAGE STEP)\n";
            cout << "        " << btc << " " << arb.coinB << " / " << arb.priceCB_real 
                 << " × (1-" << FEE*100 << "%) = " << eth << " " << arb.coinC << "\n";
            
            double ethFair = (btc / arb.priceCB_fair) * (1 - FEE);
            cout << "        (At fair price: " << ethFair << " " << arb.coinC << ")\n";
            cout << "        Extra gained: +" << setprecision(4) << (eth - ethFair) << " " << arb.coinC << "\n\n";
            
            double usdt = eth * arb.priceAC * (1 - FEE);
            cout << "Step 3: Sell " << arb.coinC << " for " << arb.coinA << "\n";
            cout << "        " << setprecision(6) << eth << " " << arb.coinC << " × $" << setprecision(2) << arb.priceAC
                 << " × (1-" << FEE*100 << "%) = " << usdt << " " << arb.coinA << "\n\n";
            
            cout << "═══════════════════════════════════════════════════════════════\n";
            cout << "  RESULT:\n";
            cout << "  Starting: " << capital << " " << arb.coinA << "\n";
            cout << "  Ending:   " << usdt << " " << arb.coinA << "\n";
            cout << "  Profit:   " << (usdt - capital) << " " << arb.coinA 
                 << " (" << ((usdt/capital - 1) * 100) << "%)\n";
            cout << "═══════════════════════════════════════════════════════════════\n";
        } else {
            // Counter-clockwise: USDT -> ETH -> BTC -> USDT
            double eth = (capital / arb.priceAC) * (1 - FEE);
            cout << "Step 1: Buy " << arb.coinC << " with " << arb.coinA << "\n";
            cout << "        " << capital << " " << arb.coinA << " / $" << arb.priceAC 
                 << " × (1-" << FEE*100 << "%) = " << setprecision(6) << eth << " " << arb.coinC << "\n\n";
            
            double btc = (eth * arb.priceCB_real) * (1 - FEE);
            cout << "Step 2: Sell " << arb.coinC << " for " << arb.coinB << " (ARBITRAGE STEP)\n";
            cout << "        " << eth << " " << arb.coinC << " × " << arb.priceCB_real 
                 << " × (1-" << FEE*100 << "%) = " << btc << " " << arb.coinB << "\n\n";
            
            double usdt = btc * arb.priceAB * (1 - FEE);
            cout << "Step 3: Sell " << arb.coinB << " for " << arb.coinA << "\n";
            cout << "        " << btc << " " << arb.coinB << " × $" << setprecision(2) << arb.priceAB
                 << " × (1-" << FEE*100 << "%) = " << usdt << " " << arb.coinA << "\n\n";
            
            cout << "═══════════════════════════════════════════════════════════════\n";
            cout << "  RESULT:\n";
            cout << "  Starting: " << capital << " " << arb.coinA << "\n";  
            cout << "  Ending:   " << usdt << " " << arb.coinA << "\n";
            cout << "  Profit:   " << (usdt - capital) << " " << arb.coinA 
                 << " (" << ((usdt/capital - 1) * 100) << "%)\n";
            cout << "═══════════════════════════════════════════════════════════════\n";
        }
    }
    
    void scanAllTriangles(
        const vector<string>& coins,
        const map<pair<string,string>, double>& prices
    ) {
        cout << "\n╔══════════════════════════════════════════════════════════════╗\n";
        cout << "║              SCANNING ALL TRIANGULAR OPPORTUNITIES           ║\n";
        cout << "╚══════════════════════════════════════════════════════════════╝\n\n";
        
        vector<TriangularArbitrage> opportunities;
        
        string quote = "USDT";
        
        for (size_t i = 0; i < coins.size(); ++i) {
            if (coins[i] == quote) continue;
            
            for (size_t j = i + 1; j < coins.size(); ++j) {
                if (coins[j] == quote) continue;
                
                auto keyBQ = make_pair(coins[i], quote);
                auto keyCQ = make_pair(coins[j], quote);
                auto keyCB = make_pair(coins[j], coins[i]);
                
                if (prices.count(keyBQ) && prices.count(keyCQ) && prices.count(keyCB)) {
                    auto arb = detectOpportunity(
                        quote, coins[i], coins[j],
                        prices.at(keyBQ), prices.at(keyCQ), prices.at(keyCB)
                    );
                    
                    if (arb.profit > 0) {
                        opportunities.push_back(arb);
                    }
                }
            }
        }
        
        sort(opportunities.begin(), opportunities.end(),
             [](const TriangularArbitrage& a, const TriangularArbitrage& b) {
                 return a.profit > b.profit;
             });
        
        if (opportunities.empty()) {
            cout << "No profitable arbitrage opportunities found.\n";
            return;
        }
        
        cout << "Found " << opportunities.size() << " profitable opportunities:\n\n";
        cout << left << setw(20) << "Triangle" << setw(15) << "Fair Price" 
             << setw(15) << "Actual Price" << setw(12) << "Deviation" << "Profit\n";
        cout << string(70, '-') << "\n";
        
        for (auto& arb : opportunities) {
            cout << setw(20) << (arb.coinA + "-" + arb.coinB + "-" + arb.coinC)
                 << setw(15) << fixed << setprecision(6) << arb.priceCB_fair
                 << setw(15) << arb.priceCB_real
                 << setw(12) << setprecision(2) << arb.deviation << "%"
                 << setprecision(4) << arb.profit << "%\n";
        }
    }
};

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(nullptr);

    ArbitrageDetector detector;
    
    // ═══════════════════════════════════════════════════════════════
    // EXAMPLE 1: Exact scenario from user's description
    // ═══════════════════════════════════════════════════════════════
    cout << "╔══════════════════════════════════════════════════════════════╗\n";
    cout << "║     EXAMPLE: User's Scenario (ETH/BTC underpriced)          ║\n";
    cout << "╚══════════════════════════════════════════════════════════════╝\n";
    
    double BTC_USDT = 50000.0;   // 1 BTC = $50,000
    double ETH_USDT = 3000.0;    // 1 ETH = $3,000
    double ETH_BTC = 0.055;      // Actual market price (should be 0.06)
    
    auto arb = detector.detectOpportunity("USDT", "BTC", "ETH", BTC_USDT, ETH_USDT, ETH_BTC);
    detector.simulateTrade(arb, 10000.0);
    
    // ═══════════════════════════════════════════════════════════════
    // EXAMPLE 2: Scan multiple triangles
    // ═══════════════════════════════════════════════════════════════
    vector<string> coins = {"USDT", "BTC", "ETH", "BNB", "SOL", "XRP"};
    
    map<pair<string,string>, double> prices;
    
    // Base prices against USDT
    prices[{"BTC", "USDT"}] = 104000;
    prices[{"ETH", "USDT"}] = 3950;
    prices[{"BNB", "USDT"}] = 720;
    prices[{"SOL", "USDT"}] = 220;
    prices[{"XRP", "USDT"}] = 2.45;
    
    // Cross pairs (with some "inefficiencies" for arbitrage)
    prices[{"ETH", "BTC"}] = 0.0375;     // Fair: 3950/104000 = 0.03798 -> slightly lower
    prices[{"BNB", "BTC"}] = 0.00685;    // Fair: 720/104000 = 0.00692 -> slightly lower  
    prices[{"SOL", "BTC"}] = 0.00215;    // Fair: 220/104000 = 0.00211 -> slightly higher
    prices[{"BNB", "ETH"}] = 0.180;      // Fair: 720/3950 = 0.1823 -> slightly lower
    prices[{"SOL", "ETH"}] = 0.0565;     // Fair: 220/3950 = 0.0557 -> slightly higher
    prices[{"XRP", "BTC"}] = 0.0000232;  // Fair: 2.45/104000 = 0.0000236
    
    detector.scanAllTriangles(coins, prices);
    
    // ═══════════════════════════════════════════════════════════════
    // EXAMPLE 3: Simulate best opportunity
    // ═══════════════════════════════════════════════════════════════
    cout << "\n";
    auto arb2 = detector.detectOpportunity("USDT", "BTC", "ETH", 
        prices[{"BTC", "USDT"}], prices[{"ETH", "USDT"}], prices[{"ETH", "BTC"}]);
    detector.simulateTrade(arb2, 10000.0);

    return 0;
}
