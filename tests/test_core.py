from synergy_trademux.core import *

def test_cheapest_first():
    q=[VenueQuote('A',100,50,5,5,10),VenueQuote('B',100,100,1,1,20)]
    p=smart_route(60,q)
    assert p.slices[0].venue=='B' and p.unfilled_notional==0

def test_capacity_split():
    q=[VenueQuote('A',100,30,1,1,10),VenueQuote('B',100,50,2,1,20)]
    p=smart_route(70,q)
    assert len(p.slices)==2 and p.unfilled_notional==0
