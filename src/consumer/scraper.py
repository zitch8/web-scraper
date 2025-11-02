from abc import ABC, abstractmethod


class ScraperInterface(ABC):

    @abstractmethod
    def fetch_data(self, url: str, headers: str,  ) -> str:
        """
        Fetch data from the given URL
        
        Args:
            url (str): The URL to fetch data from
            headers: 
        """
        pass

    @abstractmethod
    def parse_data(self, raw_data: str) -> dict:
        """
        Parse the raw data and return structured information
        
        Args:
            raw_data (str): The raw data to parse
        
        Returns:
        """