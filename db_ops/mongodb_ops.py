import logging
import os

logging.basicConfig(filename="video_scraper.log", level=logging.INFO, format="%(name)s:%(levelname)s:%(asctime)s:%(message)s" )
import pymongo
from dotenv import load_dotenv


def insert_data(db_name, data):
    logging.info("Inseting data to Mongodb database %s.." % db_name)
    try :
        load_dotenv()
        user = os.environ.get('USER')
        passwd = os.environ.get('pass')
        client = pymongo.MongoClient(f"mongodb+srv://{user}:{passwd}@cluster0.zeesz.mongodb.net/?retryWrites=true&w=majority")
    except Exception as e:
        logging.exception(e)
        raise e

    # create a database or use existing one
    db = client[db_name]

    # create or use table
    video_data = db["videodata"]

    try :
        video_data.insert_one(data)
        logging.info("Data inserted successfully.")
    except Exception as e:
        logging.exception(e)
        raise e
    finally:
        client.close()

def fetch_data(db_name, table_name):
    logging.info("Fetching data from %s , %s..".format(db_name,table_name) )
    try :
        load_dotenv()
        user = os.environ.get('USER')
        passwd = os.environ.get('pass')
        client = pymongo.MongoClient(
            f"mongodb+srv://{user}:{passwd}@cluster0.zeesz.mongodb.net/?retryWrites=true&w=majority")
        db = client[db_name]
        table = db[table_name]
        data = table.find()
    except Exception as e:
        logging.exception(e)

    results = []

    while True:
        try :
            results.append(data.next())
        except StopIteration as e:
            break
        except Exception as e:
            logging.exception(e)
        finally:
            client.close()
    logging.info("Fetching data complete.")
    return results

