from pydantic import BaseModel

class ExtractedDetail(BaseModel):
    figure:float
    context:str
    importance:int

class DetailResponse(BaseModel):
    response: list[ExtractedDetail]


class ExtractedOutlook(BaseModel):
    outlook:str
    importance:int

class OutlookResponse(BaseModel):
    response:list[ExtractedOutlook]