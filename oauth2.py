#!/usr/bin/python3.7
'''
Util script to fetch access and refresh tokens
'''
import sys, os, webbrowser, yaml, asyncio, pprint

from aiogoogle import Aiogoogle
from aiogoogle.excs import HTTPError
from aiogoogle.auth.utils import create_secret
from aiogoogle.auth.managers import OOB_REDIRECT_URI

try:
    with open("keys.yaml", "r") as stream:
        config = yaml.load(stream)
except Exception as e:
    print("Rename _keys.yaml to keys.yaml")
    raise e

EMAIL = config["user_creds"]["email"]
CLIENT_CREDS = {
    "client_id": config["client_creds"]["client_id"],
    "client_secret": config["client_creds"]["client_secret"],
    "scopes": config["client_creds"]["scopes"],
    "redirect_uri": OOB_REDIRECT_URI,
}


async def main():
    aiogoogle = Aiogoogle(client_creds=CLIENT_CREDS)
    uri = aiogoogle.oauth2.authorization_url(
        client_creds=CLIENT_CREDS,
        access_type="offline",
        include_granted_scopes=True,
        prompt="select_account",
    )
    webbrowser.open_new_tab(uri)
    grant = input("Paste the code you received here, then press Enter")
    full_user_creds = await aiogoogle.oauth2.build_user_creds(
        grant=grant, client_creds=CLIENT_CREDS
    )
    print(
        f"full_user_creds: {pprint.pformat(full_user_creds)}"
    )


if __name__ == "__main__":
    asyncio.run(main())
