from enum import Enum
from dataclasses import dataclass

class Priority(Enum):
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

@dataclass
class Article():
    id: str
    url: str
    source: str
    category: str
    priority: str
    
    # def __post__init__(self):
    #     self.validate()

    def validate(self):
        if not isinstance(self.id, str):
            raise ValueError("Article id must be a string")
        if not isinstance(self.url, str) or not self.url.startswith(('http://', 'https://')):
            raise ValueError("Article url must be a valid url string")
        if not isinstance(self.source, str):
            raise ValueError("Article source must be a string")
        if not isinstance(self.category, str):
            raise ValueError("Article category must be a string")
        if not isinstance(self.priority, str):
            raise ValueError("Article priority must be a string")
        else:
            try:
                self.priority = Priority(self.priority.lower())
            except ValueError:
                raise ValueError("Article priority must be one of: high, medium, low")
            
        return True

        # TODO: Parse priority to Priority class
