from typing import List
from pydantic import BaseModel

class SuccessResponse(BaseModel):
    message: str
    
class MultipleResponse(BaseModel):
    messages: List[str]
