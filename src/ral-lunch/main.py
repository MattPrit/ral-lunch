import httpx
from bs4 import BeautifulSoup, SoupStrainer
import io
from pathlib import Path
import tabula
import pandas as pd
from functools import cache
from datetime import date
from fastapi import FastAPI, HTTPException, Depends
from typing import Optional


PAGE_URL = "https://www.ralcatering.com/menu"
LOCAL_PDF_FILE = Path(__file__).parent / "menu.pdf"

def _get_current_week_num():
    return date.today().isocalendar()[1]


def _get_pdf_link(week=1):
    response = httpx.get(PAGE_URL)
    if httpx.codes.is_error(response.status_code):
        raise HTTPException(500, "Unable to get menu data.")
    for link in BeautifulSoup(response, "html.parser", parse_only=SoupStrainer("a")):
        if not link.has_attr("href"):
            continue
        link_href = link["href"]
        if ".pdf" in link_href:
            return link_href
    raise HTTPException(500, "Unable to get menu data.")


def _get_menu_pdf(pdf_link: str):
    response = httpx.get(pdf_link)
    if httpx.codes.is_error(response.status_code):
        raise HTTPException(500, "Unable to get menu data.")
    return response.content


def _get_menu_table_from_pdf(pdf_content: bytes):
    with io.BytesIO(pdf_content) as open_pdf_file:
        tables = tabula.read_pdf(
            open_pdf_file,
            pages=1,
            pandas_options={
                "columns": [
                    "Type",
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                ],
                "dtype": str,
            },
        )
    menu_table = tables[0]
    menu_table.drop([0])
    menu_table[:] = menu_table[:].astype(str)
    menu_table["Type"][[9, 10]] = "Sides"
    menu_table["Type"][[13, 14, 15, 16]] = "Jacket Potato"
    menu_table["Type"][[18, 19, 20]] = "Snack"
    for col in menu_table.columns:
        menu_table[col] = menu_table[col].map(lambda x: x.replace("\r", ""))
    return menu_table


@cache
def _get_menu_data(week_num: int):
    pdf_link = _get_pdf_link()
    menu_pdf = _get_menu_pdf(pdf_link)
    menu_table = _get_menu_table_from_pdf(menu_pdf)

    def _get_values_from_table(day: str, type: str) -> list[str]:
        return list(menu_table[day][menu_table["Type"] == type].values)

    data = {
        day.upper(): {
            "SOUP": {
                "Vegetable": ",\n\t".join(
                    _get_values_from_table(day, "VegetableSoup £1.05")
                ),
                "Meat": ",\n\t".join(_get_values_from_table(day, "Meat Soup£1.35")),
            },
            "MAIN": {
                "Regular": ",\n\t".join(
                    _get_values_from_table(day, "ClassicMain Course£4.35")
                ),
                "Vegetarian": ",\n\t".join(
                    _get_values_from_table(day, "VegetarianMain Course£3.55")
                ),
            },
            "THEATRE": ",\n\t".join(
                _get_values_from_table(day, "Theatre£5.25")
                + _get_values_from_table(day, "Veg Option")
            ),
            "SPECIAL": "".join(_get_values_from_table(day, "Special")),
            "SIDES": _get_values_from_table(day, "Sides"),
            "DELI": ",\n\t".join(_get_values_from_table(day, "Hot Deli£4.25")),
            "DESSERT": "".join(_get_values_from_table(day, "Hot Dessert£1.45")),
            "POTATO": _get_values_from_table(day, "Jacket Potato"),
            "SNACK": _get_values_from_table(day, "Snack"),
        }
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    }
    return data


def get_menu_data():
    yield _get_menu_data(_get_current_week_num())


app = FastAPI()


@app.get("/menu")
def get_menu(
    day: Optional[str] = None,
    meal_type: Optional[str] = None,
    menu_data: dict = Depends(get_menu_data),
):
    if day is None and meal_type is None:
        return menu_data
    if day is not None:
        if day.upper() not in menu_data.keys():
            raise HTTPException(404, f"Day '{day}' not recognised'")
        if meal_type is None:
            return menu_data[day.upper()]
        if meal_type.upper() not in menu_data[day.upper()].keys():
            raise HTTPException(404, f"Meal type '{meal_type}' not recognised'")
        return menu_data[day.upper()][meal_type.upper()]
    if meal_type.upper() not in menu_data["MONDAY"].keys():
        raise HTTPException(404, f"Meal type '{meal_type}' not recognised'")
    return {d: menu_data[d][meal_type.upper()] for d in menu_data.keys()}


@app.get("/menu/day/{day}")
def get_days_menu(day: str):
    return get_menu(day=day)


@app.get("/menu/meal_type/{meal_type}")
def get_days_menu(meal_type: str):
    return get_menu(meal_type=meal_type)
