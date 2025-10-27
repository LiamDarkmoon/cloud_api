from supabase import create_client, Client
from config import config

url = config.DB_URL
key = config.DB_KEY

supabase: Client = create_client(url, key)


def db() -> Client:
    return supabase
