from typing import Annotated, Optional

import pandas as pd
import uvicorn
from config_db import Cars, session
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi_mcp import FastApiMCP
from helpers import populate_db
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select


class FilterParams(BaseModel):
    see_available_values: Optional[str] = Field(
        None,
        description="If you want to see the available values for a specific column, pass the column name here. Example: see_available_values=marca it return all distinct values for marca column and the qty of cars for each value, this can help you to choose better parameters to find the car you want.",
    )
    marca: Optional[str] = Field(
        None,
        description="Brand of the car. Accept a single value or multiple values separated by commas. Example: 'Toyota,Honda,Ford' (Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    modelo: Optional[str] = Field(
        None,
        description="Model of the car. Accept a single value or multiple values separated by commas. Example: 'Camry,Accord,Civic' (Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    motorizacao: Optional[str] = Field(
        None,
        description="Engine size of the car. Accept a single value or multiple values separated by commas. Example: '2.0,2.5,3.0' (Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    tipo_combustivel: Optional[str] = Field(
        None,
        description="Fuel type of the car. Accept a single value or multiple values separated by commas. Example: 'Gasoline,Diesel,Electric'(Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    cor: Optional[str] = Field(
        None,
        description="Color of the car. Accept a single value or multiple values separated by commas. Example: 'Black,White,Red'(Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    transmissao: Optional[str] = Field(
        None,
        description="Transmission type of the car. Accept a single value or multiple values separated by commas. Example: 'Automatic,Manual'(Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    categoria: Optional[str] = Field(
        None,
        description="Category of the car. Accept a single value or multiple values separated by commas. Example: 'Sedan,SUV,Coupe'(Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    ano_min: Optional[int] = Field(
        None,
        description="Minimum year of the car. Example: 2020. Real name in database is 'ano', but to make it more intuitive for LLM, we can use this suffixes to filter numeric values, for example: ano_min and ano_max. (Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    ano_max: Optional[int] = Field(
        None,
        description="Maximum year of the car. Example: 2023. Real name in database is 'ano', but to make it more intuitive for LLM, we can use this suffixes to filter numeric values, for example: ano_min and ano_max. (Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    quilometragem_min: Optional[int] = Field(
        None,
        description="Minimum mileage of the car. Example: 10000. Real name in database is 'quilometragem', but to make it more intuitive for LLM, we can use this suffixes to filter numeric values, for example: quilometragem_min and quilometragem_max. (Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    quilometragem_max: Optional[int] = Field(
        None,
        description="Maximum mileage of the car, if you want a brand new car pass 0, if you want a semi-new car pass a value less than 30000. Example: 100000. Real name in database is 'quilometragem', but to make it more intuitive for LLM, we can use this suffixes to filter numeric values, for example: quilometragem_min and quilometragem_max. (Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    numero_de_portas_min: Optional[int] = Field(
        None,
        description="Minimum number of doors of the car. Example: 2. Real name in database is 'numero_de_portas', but to make it more intuitive for LLM, we can use this suffixes to filter numeric values, for example: numero_de_portas_min and numero_de_portas_max. (Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    numero_de_portas_max: Optional[int] = Field(
        None, description="Maximum number of doors of the car. Example: 4"
    )
    preco_min: Optional[float] = Field(
        None,
        description="Minimum price of the car. Example: 10000.00. Real name in database is 'preco', but to make it more intuitive for LLM, we can use this suffixes to filter numeric values, for example: preco_min and preco_max. (Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    preco_max: Optional[float] = Field(
        None,
        description="Maximum price of the car. Example: 100000.00. Real name in database is 'preco', but to make it more intuitive for LLM, we can use this suffixes to filter numeric values, for example: preco_min and preco_max. (Database is dinamically updated, so if you want to know the distinct values for this column, pass see_available_values=column_name)",
    )
    order_by: Optional[str] = Field(
        None,
        description="Can order by using columns like: 'km_por_litro' if you want to order by fuel efficiency or 'preco' if you want to get more valueables or cheapest, 'numero_de_portas', 'quilometragem', 'ano'. for example: order_by=km_por_litro_desc or order_by=preco_asc",
    )
    limit: Optional[int] = Field(
        100,
        description="Limit the number of cars returned. You can force it to be less than 10 to make the dialog more dynamic if user wants. Example: limit=10",
    )


app = FastAPI()
mcp = FastApiMCP(app)  # Add MCP server to the FastAPI app


@app.get("/get_cars", operation_id="get_cars")
def get_cars(filter_query: Annotated[FilterParams, Query()]):
    """
    It'll receive some query string parameters and return a list of cars based on those parameters. Some rules:
    - If find more than 10 cars, keep asking the user to narrow down the search by providing more specific parameters. For it, response will be informations about columns and unique values of those columns.
    - If find less than 10 cars, return the list of cars to the user.
    - If don't find any car, return a message to the user saying that no cars match their criteria but you find others that could be interesting for them.

    List of valid query string parameters:
    - marca (VARCHAR(45))
    - modelo (VARCHAR(45))
    - motorizacao (VARCHAR(45))
    - tipo_combustivel (VARCHAR(45))
    - cor (VARCHAR(45))
    - transmissao (VARCHAR(45))
    - categoria (VARCHAR(45))

    list of numeric query string parameters, to use them requires a suffix with the operator: min and max, some examples above
    - ano_min (INTEGER)
    - ano_max (INTEGER)
    - quilometragem_min (INTEGER)
    - quilometragem_max (INTEGER)
    - numero_de_portas_min (INTEGER)
    - numero_de_portas_max (INTEGER)
    - preco_min (DECIMAL(10, 2))
    - preco_max (DECIMAL(10, 2))

    > you can use any combination of these parameters to filter the cars, for example: /get_cars?marca=Toyota&ano=2020&cor=Preto
    > you can also pass more of 1 value for the same parameter, for example: /get_cars?marca=Toyota,Honda&ano=2020&cor=Preto,Branco,azul

    List of personalized query string parameters:
    - limit (INTEGER): limit the number of cars returned, default is 100. Use this to limit 10 in case of dialog becomes too long.
    - order by (STRING): 'km_por_litro' if you want to order by fuel efficiency or 'preco' if you want to get more valueables or cheapest, 'numero_de_portas', 'quilometragem', 'ano'. for example: order_by=km_por_litro_desc or order_by=preco_asc
    """
    filter_query = filter_query.dict()  # convert to dict
    filter_query = {
        k: v for k, v in filter_query.items() if v is not None
    }  # exclude none values
    print(f"{filter_query}\n\n")

    try:
        if "limit" in filter_query.keys():
            limit = int(filter_query["limit"])
            if limit > 100:
                limit = 100
    except:
        pass

    response = {"Instruction": "", "qty_cars_finded": 0, "cars": []}
    if "see_available_values" in filter_query.keys():
        column_name = filter_query["see_available_values"]
        column = getattr(Cars, column_name, None)
        if column is None:
            return JSONResponse(content={"error": "Invalid column name"})

        stmt = select(column, func.count()).group_by(column)
        data = session.execute(stmt).all()
        response["available_values"] = {value: count for value, count in data}
        response["Instruction"] = (
            f"These are the available values for **{column_name}** column and the qty of cars for each value, you can use these information to choose better parameters to find the car you want. It include all distinct values for this column in the database and the qty of cars for each value, so isn't possible pass other parameter with this one, but you can use the values returned here to pass in other query and find the car you want."
        )
        return JSONResponse(content=response)

    stmt = select(Cars)
    for key, value in filter_query.items():
        key_check = key.replace("_min", "").replace("_max", "")

        column = getattr(Cars, key_check, None)
        if column is None:
            continue

        if "VARCHAR" in str(column.type):
            split_values = value.split(",")
            if len(split_values) > 1:
                conditions = [
                    func.lower(column) == value.lower() for value in split_values
                ]
                stmt = stmt.where(or_(*conditions))
            if len(split_values) == 1:
                stmt = stmt.where(func.lower(column) == value.lower())
        elif "INTEGER" in str(column.type) or "DECIMAL" in str(column.type):
            if key.endswith("_min"):
                stmt = stmt.where(column >= value)
            elif key.endswith("_max"):
                stmt = stmt.where(column <= value)
        else:
            print(key, str(column.type))

    # order by economico if it did send
    if "order_by" in filter_query.keys():
        column_name, order = filter_query["order_by"].rsplit("_", 1)
        column = getattr(Cars, column_name, None)
        if order == "asc":
            stmt = stmt.order_by(column.asc())
        elif order == "desc":
            stmt = stmt.order_by(column.desc())

    stmt = stmt.limit(limit)
    # return {'select': str(stmt)}

    data_cars = session.execute(stmt).scalars().all()
    # return {'qt_carros': int(len(data_cars))}

    df = pd.DataFrame([car.to_dict() for car in data_cars])
    if df.empty:
        response["Instruction"] = (
            "We dont find any car, return a message to the user saying that no cars match their criteria but you can find others that could be interesting for them."
        )

    if len(df) > 0 and len(df) <= 10:
        response["Instruction"] = "List this options to user."
        response["qty_cars_finded"] = len(df)
        df["preco"] = df["preco"].map(
            lambda x: float(x)
        )  # convert to float to JSONRESPONSE works
        response["cars"] = df.to_dict(orient="records")

    if len(df) > 10:
        response["Instruction"] = (
            "We find more than 10 cars, can you provide more specific parameters to narrow down the search ? Above has the qty of each value for each column, you can use these information to ask more specific questions to user and find the best option for them."
        )
        response["qty_cars_finded"] = len(df)

        for col in df.columns:
            if col in ["id", "descricao", "ano", "km_por_litro", "preco"]:
                continue
            values = df[col].unique()
            df.groupby(col).size()
            if len(values) > 1:
                response["Instruction"] += f"**{col}**\n"
                for value in values:
                    response[
                        "Instruction"
                    ] += f"- {value} ({df.groupby(col).size()[value]})\n"

        for col in ["ano", "km_por_litro", "preco"]:
            values = df[col].unique()
            if len(values) > 1:
                response[
                    "Instruction"
                ] += f"**{col}**\n- Qty values: {len(values)} between {values.min()} and {values.max()}\n"

    return JSONResponse(content=response)


mcp.mount()  # MCP server
mcp.setup_server()  # Re-run setup, for example to registry tools.

if __name__ == "__main__":
    populate_db()
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
