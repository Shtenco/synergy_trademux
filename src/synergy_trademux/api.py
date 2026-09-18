from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from .core import VenueQuote,smart_route
app=FastAPI(title='SYNERGY TradeMux',version='2.0.0')
class Quote(BaseModel): venue:str;price:float;available_notional:float;fee_bps:float;slippage_bps:float;latency_ms:float;risk_score:float=0
class Req(BaseModel): notional:float;quotes:list[Quote]
@app.get('/health')
def health():return {'ok':True,'service':'trademux'}
@app.post('/v1/plan')
def plan(req:Req):return smart_route(req.notional,[VenueQuote(**q.model_dump()) for q in req.quotes]).to_dict()

# Enterprise v2 control/data plane
from .enterprise.service import EnterpriseRuntime, build_enterprise_router, install_observability
from .enterprise.product import build_product_router
enterprise_runtime=EnterpriseRuntime.from_env(service_name='synergy-trademux')
install_observability(app,enterprise_runtime)
app.include_router(build_enterprise_router(enterprise_runtime))
app.include_router(build_product_router(enterprise_runtime))

if __name__=='__main__':uvicorn.run(app,host='0.0.0.0',port=8000)
