from dotenv import load_dotenv; load_dotenv()
from os import getenv

from zoneinfo import ZoneInfo
from database import Database

API_DOMAIN=getenv("API_DOMAIN", "127.0.0.1")
API_PORT=int(getenv("API_PORT", "8000"))
API_PROTOCOL=getenv("API_PROTOCOL", "http")
API_FULL_LINK = API_PROTOCOL + "://" + API_DOMAIN + ":" + str(API_PORT)
API_KEYS_LENGTH=int(getenv("API_KEYS_LENGTH", "12"))

DB_HOST=getenv("DB_HOST", "localhost")
DB_DBNAME=getenv("DB_DBNAME", "postgres")
DB_PORT=getenv("DB_PORT", "5432")
DB_USER=getenv("DB_USER", "postgres")
DB_PASSWORD=getenv("DB_PASSWORD", "")
DB_OID_LENGTH=int(getenv("DB_OID_LENGTH", "4"))

tz = ZoneInfo("Europe/Moscow")
db = Database()