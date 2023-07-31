from flask import Blueprint, render_template
from wfadmin.translations.default import strings

errors = Blueprint("errors", __name__)


@errors.app_errorhandler(404)
def error_404(error):
    return (
        render_template(
            "error.html",
            code=strings["ERROR_404_TITLE"],
            message=strings["ERROR_404_MESSAGE"],
        ),
        404,
    )


@errors.app_errorhandler(403)
def error_403(error):
    return (
        render_template(
            "error.html",
            code=strings["ERROR_403_TITLE"],
            message=strings["ERROR_403_MESSAGE"],
        ),
        403,
    )


@errors.app_errorhandler(500)
def error_500(error):
    return (
        render_template(
            "error.html",
            code=strings["ERROR_500_TITLE"],
            message=strings["ERROR_500_MESSAGE"],
        ),
        500,
    )


@errors.app_errorhandler(503)
def error_503(error):
    return (
        render_template(
            "error.html",
            code=strings["ERROR_503_TITLE"],
            message=strings["ERROR_503_MESSAGE"],
        ),
        503,
    )
