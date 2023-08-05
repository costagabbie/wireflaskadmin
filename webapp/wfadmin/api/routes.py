from wfadmin import db
from pamela import authenticate, PAMError
from flask import abort, url_for, flash, make_response, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from wfadmin import db, bcrypt
from wfadmin.models import User, UserLogin, Endpoint, Peer
from wfadmin.api.utils import writeEndpointInterface,writeEndpointPeer,writePeer
from base64 import urlsafe_b64decode

api = Blueprint("api", __name__)

@api.route('/api/login')
def api_login():
    if current_user.is_authenticated:
        abort(403)
    request.environ.get('HTTP_X_REAL_IP',request.remote_addr)
    username = request.values.get('user','',str)
    password = request.values.get('pwd','',str) 
    if (len(username) > 0) and (len(password) >0):
        # If the form is being posted and passed the validations
        # we check if the user and password exist in the database
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            # the user and password checks out, do the login and redirect
            login_user(user)
            return make_response('200',200)
        else:
            # Something went wrong on the username or password
            try:
                # So we try to authenticate the user with PAM
                authenticate(username, password, "login")
                # But if the user already exist(so the password is now different)
                if user:
                    # We update the user
                    user.password = bcrypt.generate_password_hash(
                        password
                    ).decode("utf-8")
                    db.session.commit()
                else:
                    # The user doesn't exist so we create a new one
                    user = User(
                        username=username,
                        password=bcrypt.generate_password_hash(
                            password
                        ).decode("utf-8"),
                    )
                    db.session.add(user)
                    db.session.commit()
                # Login and redirect
                login_user(user)
                new_login = UserLogin(
                    user_id = user.id,
                    ip_login = request.remote_addr
                )
                db.session.add(new_login)
                db.session.commit()
                return make_response('200',200)
            except PAMError:
                # If the normal authentication failed, and subsequently the PAM
                # authentication failed, then we display the failure message
                return abort(403)
    return abort(403)

@api.route('/api/endpoint/<string:pubkey>')
def apiGetEndpointByPubKey(pubkey):
    # Check if the user is authenticated
    if not current_user.is_authenticated:
        abort(403)
    # Get the Endpoint
    endpoint = Endpoint.query.filter_by(public_key=urlsafe_b64decode(pubkey).decode()).first()
    if endpoint:
        # Generate the interface section
        configuration = writeEndpointInterface(endpoint)
        peerList = Peer.query.filter_by(endpoint=endpoint.id).all()
        #If the endpoint has peers, write the peer section for each peer
        if peerList:
            for peer in peerList:
                configuration += writeEndpointPeer(peer)
        return make_response(configuration,200)
    return abort(404)


@api.route('/api/endpoint/<int:id>')
def apiGetEndpointById(id):
    if not current_user.is_authenticated:
        abort(403)
    endpoint = Endpoint.query.get_or_404(id)
    configuration = writeEndpointInterface(endpoint)
    peerList = Peer.query.filter_by(endpoint=endpoint.id).all()
    #If the endpoint has peers, write the peer section for each peer
    if peerList:
        for peer in peerList:
            configuration += writeEndpointPeer(peer)
    return make_response(configuration,200)


@api.route('/api/peer/<string:pubkey>')
def apiGetPeerByPubkey(pubkey):
    if not current_user.is_authenticated:
        abort(403)
    peer = Peer.query.filter_by(public_key=urlsafe_b64decode(pubkey).decode()).first()
    if peer:
        configuration = writePeer(peer)
        return make_response(configuration,200)
    return abort(404)


@api.route('/api/peer/<int:id>')
def apiGetPeerById(id):
    if not current_user.is_authenticated:
        abort(403)
    peer = Peer.query.get_or_404(id)
    configuration = writePeer(peer)
    return make_response(configuration,200)