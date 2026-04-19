import requests
from bs4 import BeautifulSoup
from utility import calculate_growth

class ScraperService:

    def __init__(self, url: str):
        if not url:
            raise ValueError("URL is required")
        self.url = url

    def fetch_html(self) -> str:
        response = requests.get(self.url)
        print(response)

        response.raise_for_status()
        return response.text

    def parse_all_financial_tables(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        output = {}

        sections = soup.find_all("section", id=True)

        for section in sections:
            section_id = section.get("id")
            if not section_id:
                continue

            table = section.find("table")
            if not table:
                continue

            section_data = {}

            rows = table.find_all("tr")

            for row in rows:
                label_cell = row.find("td", class_="text")
                if not label_cell:
                    continue

                key = label_cell.get_text(strip=True).replace("+", "")
                if not key or key.lower() == "raw pdf":
                    continue

                values = []

                tds = row.find_all("td")
                for td in tds:
                    if "text" in td.get("class", []):
                        continue

                    val = td.get_text(strip=True).replace(",", "")
                    if not val:
                        continue

                    if val.endswith("%"):
                        values.append(val)
                    else:
                        try:
                            values.append(float(val))
                        except ValueError:
                            values.append(val)

                if values:
                    section_data[key] = values

            if section_data:
                output[section_id] = section_data

        return output




    def calculate_financial_growth(self, financial_data: dict):
        quarters = financial_data.get("quarters", {})


        sales = quarters.get("Sales", [])
        op_profit = quarters.get("Operating Profit", [])
        net_profit = quarters.get("Net Profit", [])

        return {
            "sales": {
                "qoq": calculate_growth(sales, 1),
                "yoy": calculate_growth(sales, 4),
            },
            "operating_profit": {
                    "qoq": calculate_growth(op_profit, 1),
                    "yoy": calculate_growth(op_profit, 4),
                },
                "net_profit": {
                    "qoq": calculate_growth(net_profit, 1),
                    "yoy": calculate_growth(net_profit, 4),
                }
            }

    def scrape(self) -> dict:
        html = self.fetch_html()
        financial_data = self.parse_all_financial_tables(html)
        growth_data = self.calculate_financial_growth(financial_data)

        return {
            "success": True,
            "data": financial_data,
            "growth": growth_data,
        }