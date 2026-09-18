from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Protocol
import uuid

@dataclass(frozen=True)
class VenueQuote:
    venue:str; price:float; available_notional:float; fee_bps:float; slippage_bps:float; latency_ms:float; risk_score:float=0.0
    def all_in_bps(self): return self.fee_bps+self.slippage_bps+self.risk_score*100.0

@dataclass(frozen=True)
class Slice:
    venue:str; notional:float; expected_price:float; expected_cost_bps:float

@dataclass(frozen=True)
class ExecutionPlan:
    correlation_id:str; slices:tuple[Slice,...]; unfilled_notional:float
    def to_dict(self):return {"correlation_id":self.correlation_id,"slices":[asdict(x) for x in self.slices],"unfilled_notional":self.unfilled_notional}

def smart_route(notional:float, quotes:list[VenueQuote], max_venues:int=4)->ExecutionPlan:
    if notional<=0: raise ValueError('notional must be positive')
    ranked=sorted(quotes,key=lambda q:(q.all_in_bps(),q.latency_ms))[:max_venues]
    remaining=notional; slices=[]
    for q in ranked:
        take=min(remaining,max(0.0,q.available_notional))
        if take>0:
            slices.append(Slice(q.venue,take,q.price,q.all_in_bps())); remaining-=take
        if remaining<=1e-12:break
    return ExecutionPlan(str(uuid.uuid4()),tuple(slices),remaining)

@dataclass
class Fill:
    venue:str; requested:float; filled:float; avg_price:float; fee:float; external_id:str

class Adapter(Protocol):
    def execute(self,symbol:str,side:str,notional:float)->Fill: ...

class PaperAdapter:
    def __init__(self,venue:str,price:float=100.0,fee_bps:float=2.0):self.venue=venue;self.price=price;self.fee_bps=fee_bps
    def execute(self,symbol,side,notional):return Fill(self.venue,notional,notional,self.price,notional*self.fee_bps/10000.0,f'paper-{uuid.uuid4().hex[:12]}')
