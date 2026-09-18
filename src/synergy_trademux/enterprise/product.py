from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from ..core import VenueQuote, smart_route
from .adapters import BybitV5Adapter, MT5Adapter, OrderRequest
from .models import Principal, Role
from .service import EnterpriseRuntime, principal_dependency, request_id_header

class QuoteModel(BaseModel):
    venue:str; price:float; available_notional:float; fee_bps:float; slippage_bps:float; latency_ms:float; risk_score:float=0
class PlanRequest(BaseModel): notional:float; quotes:list[QuoteModel]
class DispatchRequest(BaseModel):
    venue:str; symbol:str; side:str; quantity:float; order_type:str="Market"; price:float|None=None; client_order_id:str|None=None; live:bool=False; metadata:dict=Field(default_factory=dict)

def build_product_router(runtime:EnterpriseRuntime)->APIRouter:
    router=APIRouter(prefix="/enterprise/v1/execution",tags=["enterprise-trademux"])
    @router.post("/plan")
    async def plan(req:PlanRequest, principal:Principal=Depends(principal_dependency(runtime,{Role.TRADER,Role.OPERATOR})), request_id:str=Depends(request_id_header)):
        result=smart_route(req.notional,[VenueQuote(**q.model_dump()) for q in req.quotes]).to_dict();result["request_id"]=request_id
        runtime.record(principal,action="trademux.execution.plan",request_id=request_id,payload={"notional":req.notional,"slices":len(result["slices"]),"unfilled_notional":result["unfilled_notional"]})
        return result
    @router.post("/dispatch")
    async def dispatch(req:DispatchRequest, principal:Principal=Depends(principal_dependency(runtime,{Role.OPERATOR})), request_id:str=Depends(request_id_header)):
        live_allowed=req.live and os.getenv("SYNERGY_ALLOW_LIVE_EXECUTION","false").lower()=="true"
        if req.live and not live_allowed: raise HTTPException(status_code=409,detail="live execution gate is disabled")
        if req.venue.lower()=="bybit":
            adapter=BybitV5Adapter(api_key=os.getenv("BYBIT_API_KEY",""),api_secret=os.getenv("BYBIT_API_SECRET",""),allow_live=live_allowed)
        elif req.venue.lower()=="mt5":
            adapter=MT5Adapter(terminal_path=os.getenv("MT5_TERMINAL_PATH") or None,allow_live=live_allowed)
        else: raise HTTPException(status_code=400,detail="unsupported venue")
        result=adapter.execute(OrderRequest(symbol=req.symbol,side=req.side,quantity=req.quantity,order_type=req.order_type,price=req.price,client_order_id=req.client_order_id,metadata=req.metadata))
        runtime.record(principal,action="trademux.execution.dispatch",request_id=request_id,payload={"venue":req.venue,"symbol":req.symbol,"status":result.status,"live":live_allowed,"client_order_id":result.client_order_id})
        return {**result.__dict__,"request_id":request_id}
    return router
