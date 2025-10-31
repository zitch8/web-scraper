from dataclasses import dataclass

@dataclass
class Article:
    id: str
    url: str
    source: str
    category: str
    priority: str

class Publisher:
    