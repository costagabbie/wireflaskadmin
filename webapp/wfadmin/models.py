from wfadmin import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_method


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    api_key = db.Column(db.String(37),unique=True)
    dark_theme = db.Column(db.Boolean, nullable=False, default=False)
    def __repr__(self):
        return f"User('{self.username}', '{self.password}', '{self.date_creation}')"


class UserLogin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date_login = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    ip_login = db.Column(db.String(41), nullable=False)

    def __repr__(self):
        return (
            f"UserLogin({self.id},{self.user_id},'{self.date_login}','{self.ip_login}')"
        )


class Endpoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(45), unique=True, nullable=False)
    netmask = db.Column(db.Integer, nullable=False, default=32)
    public_key = db.Column(db.String(45))
    listen_port = db.Column(db.Integer, unique=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    dns = db.Column(db.String(91))
    routing_table = db.Column(db.Integer)
    mtu = db.Column(db.Integer)
    preup = db.Column(db.Text)
    postup = db.Column(db.Text)
    predown = db.Column(db.Text)
    postdown = db.Column(db.Text)
    added_by = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    date_added = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    last_modified_by = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    date_modified = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    peers = db.relationship('Peer',cascade='delete, merge, save-update')
    def __repr__(self):
        return f"Endpoint({self.id}, '{self.name}', '{self.address}', {self.netmask}, \
            {self.listen_port}, '{self.ip_address}', '{self.dns}', {self.routing_table}, \
            {self.mtu})"


class Peer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(45), unique=True, nullable=False)
    netmask = db.Column(db.Integer, nullable=False, default=32)
    endpoint = db.Column(db.Integer, db.ForeignKey("endpoint.id"), nullable=False)
    public_key = db.Column(db.String(45), nullable=False)
    keepalive = db.Column(db.Integer)
    added_by = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    date_added = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    last_modified_by = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    date_modified = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())

    def __repr__(self):
        return f"Peer({self.id}, '{self.name}', '{self.address}', '{self.endpoint}', '{self.public_key}', {self.keepalive})"

    @hybrid_method
    def endpoint_name(self):
        endpoint = Endpoint.query.get(self.endpoint)
        return endpoint.name
    
    @hybrid_method
    def endpoint_pubkey(self):
        endpoint = Endpoint.query.get(self.endpoint)
        return endpoint.public_key

    @hybrid_method
    def endpoint_ipaddress(self):
        endpoint = Endpoint.query.get(self.endpoint)
        return f'{endpoint.ip_address}:{endpoint.listen_port}'
    
    @hybrid_method
    def endpoint_address(self):
        endpoint = Endpoint.query.get(self.endpoint)
        return f'{endpoint.address}/{endpoint.netmask}'