import httpx
from bs4 import BeautifulSoup, SoupStrainer
import io
from pathlib import Path
import tabula
import pandas as pd
from functools import cache
from datetime import date
from fastapi import FastAPI

PAGE_URL = "https://www.ralcatering.com/menu"
LOCAL_PDF_FILE = Path(__file__).parent / "menu.pdf"


def get_current_week_num():
    return date.today().isocalendar()[1]


@cache
def get_pdf_link(week=1):
    response = httpx.get(PAGE_URL)
    parsed_pdf_link = None
    for link in BeautifulSoup(response, "html.parser", parse_only=SoupStrainer("a")):
        if not link.has_attr("href"):
            continue
        link_href = link["href"]
        if ".pdf" in link_href:
            parsed_pdf_link = link_href
            break
    return parsed_pdf_link


@cache
def get_menu_pdf(pdf_link: str):
    # Check error status here
    return httpx.get(pdf_link).content


pdf_link = get_pdf_link()
menu_pdf = get_menu_pdf(pdf_link)

with io.BytesIO(menu_pdf) as open_pdf_file:
    tables = tabula.read_pdf(
        open_pdf_file,
        pages=1,
        pandas_options={
            "columns": ["Type", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "dtype": str,
        },
    )

table: pd.DataFrame = tables[0]
table.drop([0])
table[:] = table[:].astype(str)
table["Type"][[9, 10]] = "Sides"
table["Type"][[13, 14, 15, 16]] = "Jacket Potato"
table["Type"][[18, 19, 20]] = "Snack"
for col in table.columns:
    table[col] = table[col].map(lambda x: x.replace("\r", ""))
DAY = "Wednesday"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TYPE_TO_KEY = {
    "Vegetable Soup (£1.05)": "VegetableSoup £1.05",
    "Meat Soup (£1.35)": "Meat Soup£1.35",
    "Main Course (£4.35)": "ClassicMain Course£4.35",
    "Vegitarian Main Course (£3.55)": "VegetarianMain Course£3.55",
    "Theatre (£5.25)": "Theatre£5.25",
    "Veg Option": "Veg Option",
    "Special": "Special",
    "Sides": "Sides",
    "Hot Deli (£4.25)": "Hot Deli£4.25",
    "Hot Dessert (£1.45)": "Hot Dessert£1.45",
    "Jacket Potato": "Jacket Potato",
    "Snack": "Snack",
}
# for t, k in TYPE_TO_KEY.items():
#     print(t.upper())
#     print("\t" + ",\n\t".join(list(table[DAY][table["Type"] == k].values)))

data = {}


def get_values_from_table(day: str, type: str) -> list[str]:
    return list(table[day][table["Type"] == type].values)


for day in DAYS:
    data[day] = {
        "Soup": {
            "Vegetable": ",\n\t".join(
                get_values_from_table(day, "VegetableSoup £1.05")
            ),
            "Meat": ",\n\t".join(get_values_from_table(day, "Meat Soup£1.35")),
        },
        "Main": {
            "Regular": ",\n\t".join(
                get_values_from_table(day, "ClassicMain Course£4.35")
            ),
            "Vegetarian": ",\n\t".join(
                get_values_from_table(day, "VegetarianMain Course£3.55")
            ),
        },
        "Theatre": ",\n\t".join(
            get_values_from_table(day, "Theatre£5.25")
            + get_values_from_table(day, "Veg Option")
        ),
        "Special": "".join(get_values_from_table(day, "Special")),
        "Sides": ",\n\t".join(get_values_from_table(day, "Sides")),
        "Deli": ",\n\t".join(get_values_from_table(day, "Hot Deli£4.25")),
        "Dessert": "".join(get_values_from_table(day, "Hot Dessert£1.45")),
        "Potato": get_values_from_table(day, "Jacket Potato"),
        "Snack": get_values_from_table(day, "Snack"),
    }

app = FastAPI()
app.get("/")
def get_menu():
    return data
