from flask import Blueprint, render_template, session
from app.routes.decorators import has_package

manage_consulenze_bp = Blueprint("manage_consulenze", __name__, url_prefix="/consulenze")

@manage_consulenze_bp.route("/")
@has_package("consulenze_assicurative")
def index():
    return render_template("tools/manage_consulenze.html",
        current_tool="manage_consulenze",
        current_tool_name="📄 Consulenze Assicurative",
        user_tools=session.get("pacchetti", []),
        tool_routes={
            "manage_drivers": "manage_drivers.index",
            "fatture": "fatture.index",
            "manage_consulenze": "manage_consulenze.index"
        }
    )
