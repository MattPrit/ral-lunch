from pydantic import BaseModel, Field


class MealWithVegOption(BaseModel):
    regular: str = Field(..., alias="Regular")
    vegetarian: str = Field(..., alias="Vegetarian")


class SoupOption(BaseModel):
    vegetable: str = Field(..., alias="Vegetable")
    meat: str = Field(..., alias="Meat")


class DayMenu(BaseModel):
    soup: SoupOption = Field(..., alias="SOUP")
    main: MealWithVegOption = Field(..., alias="MAIN")
    theatre: MealWithVegOption = Field(..., alias="THEATRE")
    special: str = Field(..., alias="SPECIAL")
    sides: list[str] = Field(..., alias="SIDES")
    deli: str = Field(..., alias="DELI")
    dessert: str = Field(..., alias="DESSERT")
    potato: list[str] = Field(..., alias="POTATO")
    snack: list[str] = Field(..., alias="SNACK")


class MealTypeMenu(BaseModel):
    monday: str | list[str] | SoupOption | MealWithVegOption = Field(
        ..., alias="MONDAY"
    )
    tuesday: str | list[str] | SoupOption | MealWithVegOption = Field(
        ..., alias="TUESDAY"
    )
    wednesday: str | list[str] | SoupOption | MealWithVegOption = Field(
        ..., alias="WEDNESDAY"
    )
    thursday: str | list[str] | SoupOption | MealWithVegOption = Field(
        ..., alias="THURSDAY"
    )
    friday: str | list[str] | SoupOption | MealWithVegOption = Field(
        ..., alias="FRIDAY"
    )


class Menu(BaseModel):
    monday: DayMenu = Field(..., alias="MONDAY")
    tuesday: DayMenu = Field(..., alias="TUESDAY")
    wednesday: DayMenu = Field(..., alias="WEDNESDAY")
    thursday: DayMenu = Field(..., alias="THURSDAY")
    friday: DayMenu = Field(..., alias="FRIDAY")
