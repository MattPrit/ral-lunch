import httpx
from bs4 import BeautifulSoup, SoupStrainer
import io
from pathlib import Path
import tabula
import pandas as pd
from functools import cache
from datetime import date
from fastapi import FastAPI, HTTPException
from typing import Optional

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


def get_values_from_table(day: str, type: str) -> list[str]:
    return list(table[day][table["Type"] == type].values)


data = {
    day.upper(): {
        "SOUP": {
            "Vegetable": ",\n\t".join(
                get_values_from_table(day, "VegetableSoup £1.05")
            ),
            "Meat": ",\n\t".join(get_values_from_table(day, "Meat Soup£1.35")),
        },
        "MAIN": {
            "Regular": ",\n\t".join(
                get_values_from_table(day, "ClassicMain Course£4.35")
            ),
            "Vegetarian": ",\n\t".join(
                get_values_from_table(day, "VegetarianMain Course£3.55")
            ),
        },
        "THEATRE": ",\n\t".join(
            get_values_from_table(day, "Theatre£5.25")
            + get_values_from_table(day, "Veg Option")
        ),
        "SPECIAL": "".join(get_values_from_table(day, "Special")),
        "SIDES": get_values_from_table(day, "Sides"),
        "DELI": ",\n\t".join(get_values_from_table(day, "Hot Deli£4.25")),
        "DESSERT": "".join(get_values_from_table(day, "Hot Dessert£1.45")),
        "POTATO": get_values_from_table(day, "Jacket Potato"),
        "SNACK": get_values_from_table(day, "Snack"),
    }
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
}

app = FastAPI()


@app.get("/menu")
def get_menu(day: Optional[str] = None, meal_type: Optional[str] = None):
    if day is None and meal_type is None:
        return data
    if day is not None:
        if day.upper() not in data.keys():
            raise HTTPException(404, f"Day '{day}' not recognised'")
        if meal_type is None:
            return data[day.upper()]
        if meal_type.upper() not in data[day.upper()].keys():
            raise HTTPException(404, f"Meal type '{meal_type}' not recognised'")
        return data[day.upper()][meal_type.upper()]
    if meal_type.upper() not in data['MONDAY'].keys():
        raise HTTPException(404, f"Meal type '{meal_type}' not recognised'")
    return {
        d: data[d][meal_type.upper()] for d in data.keys()
    }


@app.get("/menu/day/{day}")
def get_days_menu(day: str):
    return get_menu(day=day)


@app.get("/menu/meal_type/{meal_type}")
def get_days_menu(meal_type: str):
    return get_menu(meal_type=meal_type)
