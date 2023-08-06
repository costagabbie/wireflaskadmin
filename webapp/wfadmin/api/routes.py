from wfadmin import db
from pamela import authenticate, PAMError
from flask import abort, url_for, flash, make_response, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from wfadmin import db, bcrypt
from wfadmin.models import User, UserLogin, Endpoint, Peer
from wfadmin.api.utils import write_endpoint_interface, write_endpoint_peer, write_peer
from base64 import urlsafe_b64decode

api = Blueprint("api", __name__)


@api.route("/api/login/<string:api_key>")
def login(api_key):
    if current_user.is_authenticated:
        return abort(403)
    user = User.query.filter_by(api_key=api_key)
    if not user :
        return abort(403)
    new_login = UserLogin(
        user_id = user.id,
        ip_login = request.remote_addr
    )
    db.session.add(new_login)
    db.session.commit()
    login_user(user)
    return make_response('200',200)



@api.route("/api/endpoint/<string:pubkey>")
def endpoint_by_pubkey(pubkey):
    # Check if the user is authenticated
    if not current_user.is_authenticated:
        abort(403)
    # Get the Endpoint
    endpoint = Endpoint.query.filter_by(
        public_key=urlsafe_b64decode(pubkey).decode()
    ).first()
    if endpoint:
        # Generate the interface section
        configuration = write_endpoint_interface(endpoint)
        peerList = Peer.query.filter_by(endpoint=endpoint.id).all()
        # If the endpoint has peers, write the peer section for each peer
        if peerList:
            for peer in peerList:
                configuration += write_endpoint_peer(peer)
        return make_response(configuration, 200)
    return abort(404)


@api.route("/api/endpoint/<int:id>")
def endpoint_by_id(id):
    if not current_user.is_authenticated:
        abort(403)
    endpoint = Endpoint.query.get_or_404(id)
    configuration = write_endpoint_interface(endpoint)
    peerList = Peer.query.filter_by(endpoint=endpoint.id).all()
    # If the endpoint has peers, write the peer section for each peer
    if peerList:
        for peer in peerList:
            configuration += write_endpoint_peer(peer)
    return make_response(configuration, 200)


@api.route("/api/peer/<string:pubkey>")
def peer_by_pubkey(pubkey):
    if not current_user.is_authenticated:
        abort(403)
    peer = Peer.query.filter_by(public_key=urlsafe_b64decode(pubkey).decode()).first()
    if peer:
        configuration = write_peer(peer)
        return make_response(configuration, 200)
    return abort(404)


@api.route("/api/peer/<int:id>")
def peer_by_id(id):
    if not current_user.is_authenticated:
        abort(403)
    peer = Peer.query.get_or_404(id)
    configuration = write_peer(peer)
    return make_response(configuration, 200)
