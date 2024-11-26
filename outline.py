# Features.py 

class RSI: 
    def __init__(self, params):
        pass
    
    def compute_value(self) -> float: 
        pass
    
class MACD: 
    def __init__(self, params): 
        pass
    
    def compute_value(self) -> float: 
        pass
    
class Hurst: 
    def __init__(self, params):
        pass 
    
    def compute_value(self) -> float: 
        pass
    
    
import backtrader as bt
    
# Strategies.py
class MomentumStrategy(bt.Strategy): 
    def __init__(self, start, end, resolution): 
        pass
    
    def add_data(self, ticker):
        pass
    
    def execute(self): 
        return self.cerebro.run()
    

        
