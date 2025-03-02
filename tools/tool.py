from abc import ABC, abstractmethod

class Tool(ABC):
    @property
    def name(self):
        pass
    @property
    def description(self):
        pass

    @property
    def params(self):
        pass

    @property
    def return_schema(self):
        pass

    @abstractmethod
    def execute(self, params):
        pass