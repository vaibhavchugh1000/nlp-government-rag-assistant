from flask import Flask, request, jsonify, render_template
from pathlib import Path

from user_pipeline import user_query_pipeline
from admin_pipeline import process_document
from get_directory_documents import get_documents


app = Flask(
    __name__,
    template_folder="gui"
)


# --------------------------------------------------
# Login GUI
# --------------------------------------------------

@app.route("/")
def home():

    return render_template(
        "login.html"
    )


# --------------------------------------------------
# Admin GUI
# --------------------------------------------------

@app.route("/admin")
def admin_page():

    documents = get_documents()

    return render_template(
        "admin.html",
        documents=documents
    )


# --------------------------------------------------
# User GUI
# --------------------------------------------------

@app.route("/user")
def user_page():

    return render_template(
        "user.html"
    )


# --------------------------------------------------
# Login API
# --------------------------------------------------

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    user_id = data.get("id")
    password = data.get("password")

    if user_id == "user" and password == "user":

        return jsonify({
            "success": True,
            "role": "user"
        })

    elif user_id == "admin" and password == "admin":

        return jsonify({
            "success": True,
            "role": "admin"
        })

    else:

        return jsonify({
            "success": False,
            "message": "Invalid ID or password"
        }), 401


# --------------------------------------------------
# User Query API
# --------------------------------------------------

@app.route("/user/query", methods=["POST"])
def user_query():

    data = request.get_json()

    query = data.get("query")

    if not query or not query.strip():

        return jsonify({
            "success": False,
            "message": "Query cannot be empty"
        }), 400

    try:

        result = user_query_pipeline(query)

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# --------------------------------------------------
# Admin Document Processing API
# --------------------------------------------------

@app.route("/admin/process", methods=["POST"])
def admin_process():

    if "document" not in request.files:

        return jsonify({
            "success": False,
            "message": "No document selected"
        }), 400


    document = request.files["document"]


    if document.filename == "":

        return jsonify({
            "success": False,
            "message": "No document selected"
        }), 400


    allowed_extensions = [
        ".pdf",
        ".docx",
        ".txt"
    ]

    extension = Path(document.filename).suffix.lower()


    if extension not in allowed_extensions:

        return jsonify({
            "success": False,
            "message": (
                "Invalid document type. "
                "Only PDF, DOCX and TXT are allowed."
            )
        }), 400


    document_path = (
        Path("data/documents")
        / document.filename
    )


    document.save(document_path)


    try:

        result = process_document(str(document_path))
                        
        return jsonify({
            "success": True,
            "result": result
        })


    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# --------------------------------------------------
# Start Flask Server
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )