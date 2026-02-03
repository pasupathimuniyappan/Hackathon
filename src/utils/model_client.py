import ai_server
from openai import AsyncOpenAI
import httpx as httpx
from ..config.settings import settings


def get_client():

    server_connection = ai_server.ServerClient(
        base=settings.base,
        access_key=settings.access_key,
        secret_key=settings.secret_key,
    )

    http_client = httpx.AsyncClient()
    http_client.cookies = server_connection.cookies

    # setup openai to point to this running instance
    client = AsyncOpenAI(
        api_key="EMPTY",
        base_url=server_connection.get_openai_endpoint(),
        default_headers=server_connection.get_auth_headers(),
        http_client=http_client,
    )

    return client
