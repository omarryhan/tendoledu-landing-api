#!/usr/bin/python3.7

import asyncio
from aiogoogle import Aiogoogle as Aiogoogle_
import yaml
import pprint
import csv

with open("keys.yaml", "r") as f:
    config = yaml.load(f)

user_creds = {
    "access_token": config["user_creds"]["access_token"],
    "refresh_token": config["user_creds"]["refresh_token"],
    "expires_at": config["user_creds"]["expires_at"],
}

client_creds = {
    "client_id": config["client_creds"]["client_id"],
    "client_secret": config["client_creds"]["client_secret"],
}

Aiogoogle = lambda: Aiogoogle_(user_creds=user_creds, client_creds=client_creds)

firestore = None


def save_docs_to_csv(documents):
    with open('signups.csv', mode='w') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(
            ['count', 'addedAt', 'email', 'expertise', 'pageName']
        )

        for i, document in enumerate(documents):
            fields = document['fields']
            writer.writerow(
                [
                    i + 1,
                    fields['addedAt']['timestampValue'],
                    fields['email']['stringValue'],
                    fields['expertise']['stringValue'],
                    fields['pageName']['stringValue']
                ]
            )


async def main():
    global firestore
    async with Aiogoogle() as google:
        firestore = await google.discover("firestore", "v1")

        resp = await google.as_user(
            firestore.projects.databases.documents.list(
                parent="projects/tendoledu/databases/(default)/documents",
                collectionId="signups",
                validate=False,  # "parent" validation has a wrong pattern. Our input is actually valid.
                pageSize=50,
            ),
            full_res=True
        )

        documents = []

        async for page in resp:
            print('fetching page')
            documents.extend(page['documents'])

        pprint.pprint(documents)

        save_docs_to_csv(documents)

if __name__ == '__main__':
    asyncio.run(main())
