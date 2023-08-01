import urllib
import sys
from pamela import authenticate, PAMError
from subprocess import check_output
from datetime import datetime
from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from wfadmin import db, bcrypt
from wfadmin.config import Config
from wfadmin.models import User, UserLogin, Endpoint, Peer
from wfadmin.main.forms import LoginForm, EndpointForm, PeerForm
from wfadmin.main.utils import SendCommand, DaemonCommandType
from wfadmin.translations.default import strings
sys.path.append('../../../common')
from common.types import CommandPacket, DaemonCommandType

main = Blueprint("main", __name__)


@main.route("/")
@main.route("/dashboard")
@login_required
def dashboard():
    ifaces = check_output(['ip', '-s' ,'link']).decode('utf-8')
    # Get the info from the system
    s = check_output("uptime").decode("utf-8")
    # Do the string manipulation magic
    uptime = s.split("  ")[0]
    load_avg = s.split("  ")[3].split(":")[1][0:-1]
    # Get the amount of peers that we have
    peer_count = db.session.query(Peer).count()
    endpoint_count = db.session.query(Endpoint).count()
    return render_template(
        "dashboard.html",
        title=strings["MENU_DASHBOARD"],
        uptime=uptime,
        load_avg=load_avg,
        peer_count=peer_count,
        endpoint_count=endpoint_count,
        ifaces=ifaces.replace('\n','<br/>')
    )


@main.route("/login", methods=["GET", "POST"])
def login():
    # If we are already authenticated then we redirect to the dashboard
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    request.environ.get('HTTP_X_REAL_IP',request.remote_addr)
    form = LoginForm()
    if form.validate_on_submit():
        # If the form is being posted and passed the validations
        # we check if the user and password exist in the database
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # the user and password checks out, do the login and redirect
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return (
                redirect(next_page)
                if next_page
                else redirect(url_for("main.dashboard"))
            )
        else:
            # Something went wrong on the username or password
            try:
                # So we try to authenticate the user with PAM
                authenticate(form.username.data, form.password.data, "login")
                # But if the user already exist(so the password is now different)
                if user:
                    # We update the user
                    user.password = bcrypt.generate_password_hash(
                        form.password.data
                    ).decode("utf-8")
                    db.session.commit()
                else:
                    # The user doesn't exist so we create a new one
                    user = User(
                        username=form.username.data,
                        password=bcrypt.generate_password_hash(
                            form.password.data
                        ).decode("utf-8"),
                    )
                    db.session.add(user)
                    db.session.commit()
                # Login and redirect
                login_user(user, remember=form.remember.data)
                new_login = UserLogin(
                    user_id = user.id,
                    ip_login = request.remote_addr
                )
                db.session.add(new_login)
                db.session.commit()
                next_page = request.args.get("next")
                return (
                    redirect(next_page)
                    if next_page
                    else redirect(url_for("main.dashboard"))
                )
            except PAMError:
                # If the normal authentication failed, and subsequently the PAM
                # authentication failed, then we display the failure message
                flash(strings["LOGIN_FAILURE"], "error")
    return render_template("login.html", title=strings["LOGIN_TITLE"], form=form)


@login_required
@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.login'))


@login_required
@main.route("/endpoints")
def list_endpoint():
    page = request.args.get("page", 1, type=int)
    endpoints = Endpoint.query.paginate(page=page, per_page=5)
    return render_template(
        "endpoint_list.html", title=strings["MENU_MANAGE_ENDPOINT"], endpoints=endpoints
    )


@login_required
@main.route("/endpoints/add", methods=["GET", "POST"])
def add_endpoint():
    form = EndpointForm()
    form.mtu.data = 1500
    form.netmask.data = 32
    form.routing_table.data = 0
    # getting our current ip address if we enabled it
    if Config.ENDPOINT_AUTOIP.upper() == "Y":
        form.ip_address.data = (
            urllib.request.urlopen("https://v4.ident.me").read().decode("utf8")
        )
    if form.validate_on_submit():
        new_endpoint = Endpoint(
            name=form.name.data,
            address=form.address.data,
            netmask=form.netmask.data,
            listen_port=form.listen_port.data,
            ip_address=form.ip_address.data,
            dns=form.dns.data,
            routing_table=form.routing_table.data,
            mtu=form.mtu.data,
            preup=form.preup.data,
            postup=form.postup.data,
            predown=form.predown.data,
            postdown=form.postdown.data,
            added_by = current_user.id,
            last_modified_by = current_user.id,
        )
        db.session.add(new_endpoint)
        db.session.commit()
        flash(strings["MANAGE_ENDPOINT_NEW_SUCCESS"], "info")
        return redirect(url_for("main.list_endpoint"))
    return render_template(
        "endpoint_add.html", title=strings["MANAGE_ENDPOINT_ADD"], form=form
    )


@login_required
@main.route("/endpoints/<int:id>/edit", methods=["GET", "POST"])
def edit_endpoint(id):
    endpoint = Endpoint.query.get_or_404(id)
    form = EndpointForm()
    # Fill the form with the already existing info
    form.name.data = endpoint.name
    form.address.data = endpoint.address
    form.netmask.data = endpoint.netmask
    form.listen_port.data = endpoint.listen_port
    form.dns.data = endpoint.dns
    form.routing_table.data = endpoint.routing_table
    form.mtu.data = endpoint.mtu
    form.preup.data = endpoint.preup
    form.postup.data = endpoint.postup
    form.predown.data = endpoint.predown
    form.postdown.data = endpoint.postdown
    if form.validate_on_submit():
        # If the new info is validated we update the record
        endpoint.name = form.name.data
        endpoint.address = form.address.data
        endpoint.netmask = form.netmask.data
        endpoint.listen_port = form.listen_port.data
        endpoint.dns = form.dns.data
        endpoint.routing_table = form.routing_table.data
        endpoint.mtu = form.mtu.data
        endpoint.preup = form.preup.data
        endpoint.postup = form.postup.data
        endpoint.predown = form.predown.data
        endpoint.postdown = form.postdown.data
        endpoint.last_modified_by = current_user.id
        endpoint.date_modified = datetime.utcnow()
        db.session.submit()
        flash(strings["MANAGE_ENDPOINT_EDIT_SUCCESS"], "info")
        return redirect(url_for("main.list_endpoint"))
    return render_template(
        "endpoint_add.html", title=strings["MANAGE_ENDPOINT_EDIT"], form=form, endpoint=endpoint
    )


@login_required
@main.route("/endpoints/<int:id>/delete", methods=["GET"])
def delete_endpoint(id):
    endpoint = Endpoint.query.get_or_404(id)
    db.session.delete(endpoint)
    flash(strings['MANAGE_ENDPOINT_DELETED'],'info')
    return redirect(url_for('main.list_endpoint'))


@login_required
@main.route("/peers")
def list_peer():
    page = request.args.get("page", 1, type=int)
    peers = Peer.query.paginate(page=page, per_page=5)
    return render_template(
        "peer_list.html", title=strings["MENU_MANAGE_PEER"], peers=peers
    )


@login_required
@main.route("/peers/add", methods=["GET", "POST"])
def add_peer():
    endpoint_count = db.session.query(Endpoint).count()
    if endpoint_count == 0:
        flash(strings["MANAGE_ENDPOINT_EMPTY"],'error')
        return redirect(url_for('main.list_peer'))
    form = PeerForm()
    form.netmask.data = 32
    if form.validate_on_submit():
        new_endpoint = Peer(
            name=form.name.data,
            address=form.address.data,
            netmask=form.netmask.data,
            endpoint=form.endpoint.data,
            public_key=form.public_key.data,
            keepalive=form.keepalive.data,
            added_by = current_user.id,
            last_modified_by = current_user.id
        )
        db.session.add(new_endpoint)
        db.session.commit()
        flash(strings["MANAGE_PEER_NEW_SUCCESS"], "info")
        return redirect(url_for("main.list_peer"))
    return render_template("peer_add.html", title=strings["MANAGE_PEER_ADD"], form=form)


@login_required
@main.route("/peers/<int:id>/edit", methods=["GET", "POST"])
def edit_peer(id):
    peer = Peer.query.get_or_404(id)
    # Fill the form with the already existing info
    form = PeerForm()
    form.name.data = peer.name
    form.address.data = peer.address
    form.netmask.data = peer.netmask
    form.public_key.data = peer.public_key
    form.keepalive.data = peer.keepalive
    if form.validate_on_submit():
        # If the new info is validated we update the record
        peer.name=form.name.data,
        peer.address=form.address.data,
        peer.netmask=form.netmask.data,
        peer.endpoint=form.endpoint.data,
        peer.public_key=form.public_key.data,
        peer.keepalive=form.keepalive.data,
        peer.last_modified_by = current_user.id
        peer.date_modified = datetime.utcnow()
        db.session.commit()
        flash(strings["MANAGE_PEER_NEW_SUCCESS"], "info")
        return redirect(url_for("main.list_peer"))
    return render_template(
        "peer_add.html", title=strings["MANAGE_PEER_EDIT"], form=form
    )


@login_required
@main.route("/peers/<int:id>/delete", methods=["GET", "POST"])
def delete_peer(id):
    peer = Peer.query.get_or_404(id)
    db.session.delete(peer)
    db.session.commit()
    flash(strings['MANAGE_PEER_DELETED'],'info')
    return redirect(url_for('main.list_peer'))
@main.route("/install")
def install():
    try:
        # if there's no tables in the database the next line will raise an exception
        usercount = db.session.query(User).count()
        flash("Already Installed", "info")
    except:
        db.create_all()  # create table
        flash("Installed", "info")
    return redirect("/")


@login_required
@main.route("/start/<int:id>")
def start_interface(id):
    endpoint = Endpoint.query.get(id)
    # if we got a valid interface or 0(all interfaces)
    if endpoint or (id == 0):
        if SendCommand(DaemonCommandType.CMD_START, id):
            flash(strings["IFACE_START_OK"], "info")
        else:
            flash(strings["IFACE_START_FAIL"], "error")
    next_page = request.args.get("next")
    return redirect(next_page) if next_page else redirect(url_for("main.dashboard"))


@login_required
@main.route("/restart/<int:id>")
def restart_interface(id):
    endpoint = Endpoint.query.get(id)
    # if we got a valid interface or 0(all interfaces)
    if endpoint or (id == 0):
        if SendCommand(DaemonCommandType.CMD_RESTART, id):
            flash(strings["IFACE_RESTART_OK"], "info")
        else:
            flash(strings["IFACE_RESTART_FAIL"], "error")
    next_page = request.args.get("next")
    return redirect(next_page) if next_page else redirect(url_for("main.dashboard"))


@login_required
@main.route("/stop/<int:id>")
def stop_interface(id):
    endpoint = Endpoint.query.get(id)
    # if we got a valid interface or 0(all interfaces)
    if endpoint or (id == 0):
        if SendCommand(DaemonCommandType.CMD_STOP, id):
            flash(strings["IFACE_STOP_OK"], "info")
        else:
            flash(strings["IFACE_STOP_FAIL"], "error")
    next_page = request.args.get("next")
    return redirect(next_page) if next_page else redirect(url_for("main.dashboard"))


@login_required
@main.route("/rebuild/<int:id>")
def rebuild_interface(id):
    endpoint = Endpoint.query.get(id)
    # if we got a valid interface or 0(all interfaces)
    if endpoint or (id == 0):
        if SendCommand(DaemonCommandType.CMD_REBUILD, id):
            flash(strings["IFACE_REBUILD_OK"], "info")
        else:
            flash(strings["IFACE_REBUILD_FAIL"], "error")
    next_page = request.args.get("next")
    return redirect(next_page) if next_page else redirect(url_for("main.dashboard"))
