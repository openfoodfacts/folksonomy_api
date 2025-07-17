#! /usr/bin/python3

from fastapi import APIRouter, Response, Depends, HTTPException, Query
from typing import Optional
from . import db
from .utils import get_current_user, check_owner_user
from .models import (
    User,
    ProductKnowledgePanels,
    TableElement,
    TableColumn,
    Element,
    Panel,
    TitleElement,
)

router = APIRouter()


@router.get(
    "/product/{product}/knowledge-panels", response_model=ProductKnowledgePanels
)
async def product_barcode_knowledge_panels(
    response: Response,
    product: str,
    k: Optional[str] = Query(None, description="Optional key to filter the results"),
    owner="",
    user: User = Depends(get_current_user),
):
    """
    Return product information in a Knowledge Panel format.
    If 'k' is provided, only that key is fetched.
    If none is provided, all the keys are returned.
    """
    check_owner_user(user, owner, allow_anonymous=True)

    query = """
        SELECT product, k, v, owner, version, editor, last_edit, comment
        FROM folksonomy
        WHERE product = %s
    """
    params = [product]
    if k:
        query += " AND k = %s"
        params.append(k)
    query += " ORDER BY k;"

    cur, timing = await db.db_exec(query, tuple(params))
    rows = await cur.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Could not find product or key",
        )

    panels_by_key = {}
    for row in rows:
        product_value, k, v, _, _, _, _, _ = row

        if k not in panels_by_key:
            panels_by_key[k] = {"Barcode": product_value, "Key": k, "Value": v}
        else:
            data = panels_by_key[k]
            if not data.get("Barcode") and product_value:
                data["Barcode"] = product_value
            if not data.get("Value") and v:
                data["Value"] = v

    panels = {}
    for k, data in panels_by_key.items():
        rows_html = ""
        for property, value in data.items():
            if value is None:
                continue

            # Links for Key and Value property
            if property == "Key":
                value_cell = (
                    f'<a href="world.openfoodfacts.org/property/{value}">{value}</a> '
                    f'<a href="wiki.openfoodfacts.org/Folksonomy/Property/{value}">&#8505;</a>'
                )
            elif property == "Value":
                value_cell = f'<a href="world.openfoodfacts.org/property/{data["Key"]}/value/{value}">{value}</a>'
            else:
                value_cell = value

            row_html = f"<tr><td>{property}</td><td>{value_cell}</td></tr>"
            rows_html += row_html

        table_html = f"<table>{rows_html}</table>"

        table_element = TableElement(
            id=k,
            title=f"Folksonomy Data for '{k}'",
            rows=table_html,
            columns=[
                TableColumn(type="text", text="Property"),
                TableColumn(type="text", text="Value"),
            ],
        )

        element = Element(type="table", table_element=table_element)

        panel = Panel(
            title_element=TitleElement(title=f"Folksonomy Data for '{k}'", name=k),
            elements=[element],
        )
        panels[k] = panel

    response_obj = ProductKnowledgePanels(knowledge_panels=panels)
    response.headers["x-pg-timing"] = timing
    return response_obj
