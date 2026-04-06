import pandas as pd
from config_db import drop_and_create_db, engine
import logging


def populate_db(use_faker: bool = False) -> bool | Exception:
    """
    Populate database with fake data.
    Args:
        use_faker (`bool`): True if you want to use fake data. When it is False will use **carros.csv** file
    Returns:
        `bool`: True when success and False if something failed.
    Examples:
        >>> populate_db()
        True
    Raises:
        Exception: If there is an error populating the database.
    """ 
    logging.info("DROPPING AND CREATING DB...")
    drop_and_create_db()

    # using CSV file.
    # if use_faker == False:
    try:
        logging.info("Populating DB with carros.csv...")
        df = pd.read_csv("carros.csv")
    except:
        msg = "Error reading carros.csv file. Please check if the file exists and is in the correct format."
        logging.error(msg)
        raise Exception(msg)
        use_faker = True

    # If want something funny, try faker data.
    # if use_faker:
    #     logging.info("Populating DB with Faker lib data...")
    # TODO
    #     df = pd.DataFrame({})

    qty = df.to_sql("tbl_cars", engine, if_exists="append", index=False)

    if qty:
        return True
    
    msg = "Error populating database. Please check if the data is in the correct format and try again."
    logging.error(msg)
    raise Exception(msg)