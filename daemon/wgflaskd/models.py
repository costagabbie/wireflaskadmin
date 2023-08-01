from sqlalchemy import Column,Integer,String,DateTime,Text,ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_method
from datetime import datetime


Base = declarative_base()

class Endpoint(Base):
    __tablename__='endpoint'
    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)
    address = Column(String(45), unique=True, nullable=False)
    netmask = Column(Integer, nullable=False, default=32)
    listen_port = Column(Integer, unique=True, nullable=False)
    ip_address = Column(String(45), nullable=False)
    dns = Column(String(91))
    routing_table = Column(Integer)
    mtu = Column(Integer)
    preup = Column(Text)
    postup = Column(Text)
    predown = Column(Text)
    postdown = Column(Text)
    added_by = Column(Integer,ForeignKey('user.id'),nullable=False)
    date_added = Column(DateTime,nullable=False,default=datetime.utcnow())
    last_modified_by = Column(Integer,ForeignKey('user.id'),nullable=False)
    date_modified = Column(DateTime,nullable=False,default=datetime.utcnow())
    def __repr__(self):
        return f"Endpoint({self.id}, '{self.name}', '{self.address}', {self.netmask}, \
            {self.listen_port}, '{self.ip_address}', '{self.dns}', {self.routing_table}, \
            {self.mtu})"


class Peer(Base):
    __tablename__='peer'
    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)
    address = Column(String(45), unique=True, nullable=False)
    netmask = Column(Integer, nullable=False, default=32)
    endpoint = Column(Integer, ForeignKey("endpoint.id"), nullable=False)
    public_key = Column(String(45), nullable=False)
    keepalive = Column(Integer)
    added_by = Column(Integer,ForeignKey('user.id'),nullable=False)
    date_added = Column(DateTime,nullable=False,default=datetime.utcnow())
    last_modified_by = Column(Integer,ForeignKey('user.id'),nullable=False)
    date_modified = Column(DateTime,nullable=False,default=datetime.utcnow())

    def __repr__(self):
        return f"Peer({self.id}, '{self.name}', '{self.address}', '{self.endpoint}', '{self.public_key}', {self.keepalive})"

    @hybrid_method
    def endpoint_name(self):
        endpoint = Endpoint.query.get(self.endpoint)
        return endpoint.name

def create_metadata(engine):
    Base.metadata.create_all(engine)