from typing import Any, List


import yaml
from pydantic import BaseModel

with open("test.yml", "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

print(data)
class Item(BaseModel):
    id:str
    type:str

class Details(BaseModel):
    name:str
    steps:List[Item]

class Flows(BaseModel):
    refund_request:Details | None = None

flows = data.get("flows",{})
results = Flows.model_validate(flows)
print(results)
print(type(results))




