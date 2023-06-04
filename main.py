from fastapi import FastAPI

app = FastAPI()


# Define a route, return a message
@app.get("/")
async def root():
    return {"message": "Hello World"}


# Use Python format strings to dynamically define routes with a path parameter
# Use type hints to correctly parse and validate path param values
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}


# FastAPI evaluates matching routes in order
# The following two routes need to be declared in this order
# Otherwise "me" could be mistaken for the user_id
@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}


# Limit possible path parameters with an Enum
from enum import Enum


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    # different ways to evaluate the ModelName
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


# Evaluation query parameters
# values for skip and limit can be defined in query params
# e.g. /items/?skip=3&limit=1
fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@app.get("/items/")
async def read_db_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]


# Required query params have no default value
# Bools get converted, so 1, True, true, on, or yes in query params all get parsed as True
# Optional query params have default value
# Notice that path param and query param are all declared together in function sig
from typing import Any

dsa = dict[str, Any]  # if we need a specify a dict key:value type


@app.get("/detailedItems/{item_id}")
async def read_item_detailed(item_id: str, short: bool, q: int | None = None):
    item: dsa = {"item_id": item_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing product with a long description"}
        )
    return item


# Send request body with POST, DELETE, PUT, PATCH (most likely POST)
# Use pytdantic BaseModel to specify the values and types to send in the body
# Can declare path, query, and body params at the same time
# Params in path are path params
# Params w/ singular type (int, str, float, bool) are query params
# More complex data type (Pydantic Model, dict, tuple, etc) are request body params
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


@app.post("/items3/{item_id}")
async def create_item(item_id: int, item: Item, q: int | None = None):
    result = {"item_id": item_id, **item.dict()}
    if item.tax:
        price_with_tax = item.price + item.tax
        result.update({"price_with_tax": price_with_tax})
    if q:
        result.update({"q": q})
    return result


# Use Type Aliases to improve readability of type hints
# Complex datatypes will be body params, so must not be GET requests

meters = float
Coordinates = tuple[meters, meters]

from math import sqrt


@app.post("/distance/")
def measure_distance(loc1: Coordinates, loc2: Coordinates) -> meters:
    d = sqrt((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2)
    return d


# Use data structure (class, dataclass, Pydantic Model) to improve readability of type hints
# Good when you need type name simplification and also a particular data structure
# NamedTuple bad idea b/c internal types not parsed by autodoc
from dataclasses import dataclass


@dataclass(frozen=True)  # immutable
class Coords:
    x: meters
    y: meters


@app.post("/distance2/")
def measure_distance2(loc1: Coords, loc2: Coords) -> meters:
    d = sqrt((loc1.x - loc2.x) ** 2 + (loc1.y - loc2.y) ** 2)
    return d


# Additional string validation of query params with Annotated and Query function
# In this case if q is provided must be 3-50 chars and start w/ capital alpha char
# But it could be None also
from typing import Annotated
from fastapi import Query

validq = Annotated[str | None, Query(min_length=3, max_length=50, regex="^[A-Z]")]


@app.get("/items4/")
async def read_items(q: validq = None):
    results: dsa = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


# Numeric validation for path parameters with Path function
# lt and gt are not indicated in Swagger autodoc, only le, ge
from fastapi import Path

validID = Annotated[int, Path(le=500, gt=1)]


@app.get("/items5/{item_id}")
async def read_items2(item_id: validID, q: str):
    results: dsa = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results


# Declare multiple body params
# User is optional (default None). If provided full_name is optional
@dataclass(frozen=True)  # immutable
class User:
    username: str
    full_name: str | None = None


@app.put("/items/{item_id}")
async def update_item(item_id: validID, item: Item, user: User | None = None):
    results = {"item_id": item_id, "item": item, "user": user}
    return results


# Force a param into the body: importance as a single int would otherwise be query param
from fastapi import Body

validImportance = Annotated[int, Body()]


@app.put("/items6/{item_id}")
async def update_item2(
    item_id: validID, item: Item, user: User, importance: validImportance
):
    results = {"item_id": item_id, "item": item, "user": user, "importance": importance}
    return results


# Use embed to force a body to include a param's name as top level, even if only one in body
validItem = Annotated[Item, Body(embed=True)]


@app.put("/items7/{item_id}")
async def update_item3(item_id: int, item: validItem):
    results = {"item_id": item_id, "item": item}
    return results


# Validate body params with Pydantic's Field
# Specify field title, default val, description, and val/length validation
from pydantic import Field

validDescription = Annotated[
    str | None,
    Field(title="The description of the item", max_length=10),
]

validPrice = Annotated[
    float, Field(gt=0, description="The price must be greater than zero")
]


class Item2(BaseModel):
    name: str
    description: validDescription = None
    price: validPrice
    tax: float | None = None


validItem2 = Annotated[Item2, Body(embed=True)]


@app.put("/items8/{item_id}")
async def update_item4(item_id: int, item: validItem2):
    results = {"item_id": item_id, "item": item}
    return results


# Pydantic models can be nested to arbitrary levels of depth
class Image(BaseModel):
    url: str
    name: str


class Item3(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: set[str] = set()
    image: Image | None = None


@app.put("/items9/{item_id}")
async def update_item5(item_id: int, item: Item3):
    results = {"item_id": item_id, "item": item}
    return results


# Pydantic has more exotic singular types that inherit from things like str, int, etc
# HttpUrl is validated as a URL and is documented as such in the autodoc
from pydantic import HttpUrl


class Image2(BaseModel):
    url: HttpUrl
    name: str


class Item4(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: set[str] = set()
    image: Image2 | None = None


@app.put("/items10/{item_id}")
async def update_item6(item_id: int, item: Item4):
    results = {"item_id": item_id, "item": item}
    return results


# You can receive request bodies of arbitrary dicts
# Even though JSON must have str keys
# If the key can be cast to int, it will be
# Kinda works, autodoc thinks the int should be a string
# Error message indicates it needs to be an integer
# No clear doc that it should be a string that can be cast to an int
# I think keys other than str for arbitrary request body dicts are anti-pattern
@app.post("/index-weights/")
async def create_index_weights(weights: dict[int, float]):
    return weights[1]
