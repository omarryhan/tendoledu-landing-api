import datetime

from sanic import Sanic, response
from secure import SecureHeaders, SecurePolicies
from aiogoogle import Aiogoogle as Aiogoogle_
import yaml


app = Sanic()

with open("keys.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

user_creds = {
    'access_token': config["user_creds"]["access_token"],
    'refresh_token': config["user_creds"]["refresh_token"],
    'expires_at': config["user_creds"]["expires_at"],
}

client_creds = {
    'client_id': config["client_creds"]['client_id'],
    'client_secret': config["client_creds"]['client_secret'],
}

Aiogoogle = lambda: Aiogoogle_(user_creds=user_creds, client_creds=client_creds)

recaptcha_private_key = config['recaptcha_private_key']

firestore = None

def secure_app():
    secure_headers = SecureHeaders()
    async def secure(request, response):
        secure_headers.sanic(response)
    app.register_middleware(secure, 'response')

secure_app()

@app.listener('before_server_start')
async def discover_firestore(app, loop):
    global firestore
    async with Aiogoogle() as google:
        firestore = await google.discover('firestore', 'v1')

@app.route('/signup/schools', methods=['POST'])
async def schools_signup_handler(request):
    pass

@app.route('/signup/students', methods=['POST'])
async def students_signup_handler(request):
    pass

@app.route('/signup/startups', methods=['POST'])
async def startups_signup_handler(request):
    pass

@app.route('/test')
async def test(request):
    email = 'test@example.com'
    expertise = 'being a bot'
    page_name = 'test'
    async with Aiogoogle() as google:
        resp = await google.as_user(
            firestore.projects.databases.documents.createDocument(
                parent='projects/tendoledu/databases/(default)/documents',
                collectionId='signups',
                json=dict(fields={
                    'email': {
                        'stringValue': email,
                    },
                    'addedAt': {
                        'timestampValue': datetime.datetime.utcnow().isoformat() + 'Z',
                    },
                    'pageName': {
                        'stringValue': page_name,
                    },
                    'expertise': {
                        'stringValue': expertise,
                    },
                }),
                validate=False,  # "parent" validation has a wrong pattern. Our pattern works fine.
            ),
            user_creds=user_creds,
        )

    return response.json(resp)

@app.route('/')
async def home(request):
    return response.json(firestore.discovery_document)

app.go_fast(port=7000)
