from flask import (
    Blueprint
)

from api.messages.messages_service import (
    get_public_message,
    get_protected_message,
    get_admin_message
)
from api.security.guards import authorization_guard

bp_name = 'api-messages'
bp_url_prefix = '/api/messages'
bp = Blueprint(bp_name, __name__, url_prefix=bp_url_prefix)


@bp.route("/public")
def public():
    return vars(get_public_message())


@bp.route("/protected")
@authorization_guard("read:protected-messages")
def protected():
    return vars(get_protected_message())


@bp.route("/admin")
@authorization_guard("read:admin-messages")
def admin():
    return vars(get_admin_message())
