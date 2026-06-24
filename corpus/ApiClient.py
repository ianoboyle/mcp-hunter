from typing import Dict, Optional, Generator, Any
import requests


class APIClient:
    def __init__(self, base_url: str, token: Optional[str] = None) -> None:
        self.base_url = base_url
        self.token = token
        self.session = requests.session()
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get_items_page(
        self,
        endpoint: Optional[str] = "",
        limit: Optional[int] = 30,
        cursor: Optional[str] = None,
    ) -> Dict:
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        url = f"{self.base_url}/{endpoint}" if endpoint else f"{self.base_url}"

        response = self.session.get(url=url, params=params)
        response.raise_for_status()
        return response.json()

    def list(
        self, endpoint: Optional[str] = None, limit: Optional[int] = 30
    ) -> Generator[Dict[str, Any], None, None]:
        cursor = None
        while True:
            page_data = self.get_items_page(endpoint, limit, cursor)

            for item in page_data.get("servers", []):
                yield item

            cursor = page_data.get("metadata").get("nextCursor", None)

            if not cursor:
                break
