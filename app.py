import datetime
import argparse

from sanic import Sanic, response
from secure import SecureHeaders, SecurePolicies
from aiogoogle import Aiogoogle as Aiogoogle_
import yaml

from sanic_wtf import SanicForm, RecaptchaField
from wtforms.validators import DataRequired, Length, ValidationError, Email, Regexp, EqualTo
from wtforms import SubmitField, StringField, BooleanField, PasswordField


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
recaptcha_public_key = '6LcOB6UUAAAAAGFpmRUeUHX66ybYyoPn-au8xyMi'

app.config.RECAPTCHA_V3_PUBLIC_KEY = recaptcha_public_key
app.config.RECAPTCHA_V3_PRIVATE_KEY = recaptcha_private_key

firestore = None

def secure_app():
    secure_headers = SecureHeaders()
    async def secure(request, response):
        secure_headers.sanic(response)
    app.register_middleware(secure, 'response')

secure_app()

class SignUpForm(SanicForm):
    page_name = StringField('Platform',[
        DataRequired(message='Missing page name.'),
        Length(min=4, max=20, message='Invalid page name length'),
        Regexp(
            r'^[a-zA-Z ]*$',
            message='Letters only'
        )
    ])
    expertise = StringField('Expertise',[
        DataRequired(message='Missing expertise.'),
        Length(min=3, max=20, message='Invalid expertise'),
        Regexp(
            r'^[a-zA-Z ]*$',
            message='Letters only'
        )
    ])
    email = StringField('Email', [
        DataRequired(message='Missing email'),
        Length(min=4, max=30, message='Invalid email length!'),
        Email(message='Invalid email')
    ])
    recaptcha_v3 = RecaptchaField(config_prefix='RECAPTCHA_V3')

@app.listener('before_server_start')
async def discover_firestore(app, loop):
    global firestore
    async with Aiogoogle() as google:
        firestore = await google.discover('firestore', 'v1')

async def post_signup_form_to_firestore(
    email,
    expertise,
    page_name
):
    async with Aiogoogle() as google:
        await google.as_user(
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
                validate=False,  # "parent" validation has a wrong pattern. Our input is actually valid.
            ),
            user_creds=user_creds,
        )

@app.route('/signup', methods=['POST'])
async def signup_handler(request):
    form = SignUpForm(request)
    valid = await form.validate_on_submit_async()
    await post_signup_form_to_firestore(
        form.email.data,
        form.expertise.data,
        form.page_name.data,
    )

    if valid is not True:
        errors = [{'msg': error[0]} for error in form.errors.values()]
        return response.json({
            'error': errors
        })
    return response.text('OK')

@app.route('/')
async def home(request):
    return response.text('Hey you! Nothing for you here.')


parser = argparse.ArgumentParser(description='Frusic Manager')
parser.add_argument('--host', default=None, help='Host')
parser.add_argument('--port', '-p', default=None, help='Port')
parser.add_argument('--debug', action='store_true', help='Debug mode')
parser.add_argument('--auto_reload', '-r', action='store_true', help='Autoreload')
parser.add_argument('--log', help='Access log', action='store_true')

if __name__ == '__main__':
    kwargv = parser.parse_args()
    app.go_fast(
        port=kwargv.port or 7000,
        host=kwargv.host,
        debug=kwargv.debug,
        auto_reload=kwargv.auto_reload,
        log=kwargv.log,
    )