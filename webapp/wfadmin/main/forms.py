from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    IntegerField,
    SelectField,
)
from wtforms.validators import DataRequired, Length, Email, IPAddress
from wfadmin.models import Endpoint
from wfadmin.translations.default import strings


class LoginForm(FlaskForm):
    username = StringField(
        strings["LOGIN_USER"],
        validators=[DataRequired(message=strings["VALIDATION_DATAREQUIRED"])],
    )
    password = PasswordField(strings["LOGIN_PASSWORD"], validators=[DataRequired()])
    remember = BooleanField(strings["LOGIN_REMEMBER"])
    submit = SubmitField(strings["BUTTON_SUBMIT"])


class EndpointForm(FlaskForm):
    name = StringField(
        strings["MANAGE_ENDPOINT_NAME"],
        validators=[
            DataRequired(message=strings["VALIDATION_DATAREQUIRED"]),
            Length(min=3, max=20),
        ],
    )
    public_key = StringField(
        strings["MANAGE_PEER_NEW_PUBKEY"],
        validators=[
            DataRequired(message=strings["VALIDATION_DATAREQUIRED"]),
            Length(min=44,max=44)
        ],
    )
    address = StringField(
        strings["MANAGE_ENDPOINT_ADDRESS"],
        validators=[
            DataRequired(message=strings["VALIDATION_DATAREQUIRED"]),
            IPAddress(True, True, strings["VALIDATION_IP"]),
        ],
    )
    netmask = IntegerField(
        strings["MANAGE_ENDPOINT_NETMASK"],
        validators=[DataRequired(message=strings["VALIDATION_DATAREQUIRED"])],
    )
    listen_port = IntegerField(
        strings["MANAGE_ENDPOINT_LISTENPORT"],
        validators=[DataRequired(message=strings["VALIDATION_DATAREQUIRED"])],
    )
    ip_address = StringField(
        strings["MANAGE_ENDPOINT_IPADDRESS"],
        validators=[
            DataRequired(message=strings["VALIDATION_DATAREQUIRED"]),
            IPAddress(True, True, strings["VALIDATION_IP"]),
        ],
    )
    dns = StringField(
        strings["MANAGE_ENDPOINT_DNS"]
    )
    routing_table = IntegerField(strings["MANAGE_ENDPOINT_TABLE"])
    mtu = IntegerField(
        strings["MANAGE_ENDPOINT_MTU"],
        validators=[DataRequired(message=strings["VALIDATION_DATAREQUIRED"])],
    )
    preup = StringField(strings["MANAGE_ENDPOINT_PREUP"], validators=[Length(max=4096)])
    postup = StringField(
        strings["MANAGE_ENDPOINT_POSTUP"], validators=[Length(max=4096)]
    )
    predown = StringField(
        strings["MANAGE_ENDPOINT_PREDOWN"], validators=[Length(max=4096)]
    )
    postdown = StringField(
        strings["MANAGE_ENDPOINT_POSTDOWN"], validators=[Length(max=4096)]
    )
    submit = SubmitField(strings["BUTTON_SUBMIT"])


class PeerForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint.choices = [
            (endpoint.id, endpoint.name) for endpoint in Endpoint.query.all()
        ]

    name = StringField(
        strings["MANAGE_PEER_NAME"],
        validators=[
            DataRequired(strings["VALIDATION_DATAREQUIRED"]),
            Length(min=3, max=20),
        ],
    )
    address = StringField(
        strings["MANAGE_PEER_NEW_ALLOWEDIP"],
        validators=[DataRequired(), IPAddress(True, True, strings["VALIDATION_IP"])],
    )
    netmask = IntegerField(
        strings["MANAGE_PEER_NETMASK"],
        validators=[DataRequired(message=strings["VALIDATION_DATAREQUIRED"])],
    )
    endpoint = SelectField(
        strings["MANAGE_PEER_NEW_ENDPOINTIP"],
        validators=[DataRequired(strings["VALIDATION_DATAREQUIRED"])],
    )
    public_key = StringField(
        strings["MANAGE_PEER_NEW_PUBKEY"],
        validators=[
            DataRequired(strings["VALIDATION_DATAREQUIRED"]),
            Length(min=44, max=44),
        ],
    )
    keepalive = IntegerField(strings["MANAGE_PEER_NEW_KEEPALIVE"])
    submit = SubmitField(strings["BUTTON_SUBMIT"])
