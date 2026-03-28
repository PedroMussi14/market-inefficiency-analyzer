from arbitrage import is_arbitrage, calculate_stakes, calculate_profit
from sample_data import events

bankroll = 100

for event in events:
    odds = event["odds"]
    
    print(f"\nEvent: {event['event']}")
    
    if is_arbitrage(odds):
        stakes = calculate_stakes(bankroll, odds)
        profit = calculate_profit(bankroll, stakes, odds)
        
        print("Arbitrage found!")
        for i, stake in enumerate(stakes):
            print(f"Bet {i+1}: ${stake:.2f} at odds {odds[i]}")
        
        print(f"Guaranteed profit: ${profit:.2f}")
    else:
        print("No arbitrage opportunity.")