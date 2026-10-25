from flask import Flask, request, jsonify, render_template
from pathlib import Path
from werkzeug.utils import secure_filename

from user_pipeline import user_query_pipeline
from admin_pipeline import process_document
from get_directory_documents import get_documents


app = Flask(
    __name__,
    template_folder="gui"
)

# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BASE_DIR / "data" / "documents"

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}

# Ensure the document directory exists
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# Login GUI
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("login.html")


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
    return render_template("user.html")


# --------------------------------------------------
# Login API
# --------------------------------------------------

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

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

    return jsonify({
        "success": False,
        "message": "Invalid ID or password"
    }), 401


# --------------------------------------------------
# User Query API
# --------------------------------------------------

@app.route("/user/query", methods=["POST"])
def user_query():
    data = request.get_json(silent=True) or {}

    query = data.get("query")

    if not isinstance(query, str) or not query.strip():
        return jsonify({
            "success": False,
            "message": "Query cannot be empty"
        }), 400

    try:
        result = user_query_pipeline(query.strip())

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception:
        app.logger.exception("User query processing failed")

        return jsonify({
            "success": False,
            "message": (
                "Unable to process the query. "
                "Please check the server logs."
            )
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

    if not document.filename:
        return jsonify({
            "success": False,
            "message": "No document selected"
        }), 400

    # Validate and sanitize the filename
    original_filename = document.filename
    safe_filename = secure_filename(original_filename)

    if not safe_filename:
        return jsonify({
            "success": False,
            "message": "Invalid document filename"
        }), 400

    extension = Path(safe_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({
            "success": False,
            "message": (
                "Invalid document type. "
                "Only PDF, DOCX and TXT are allowed."
            )
        }), 400

    document_path = DOCUMENTS_DIR / safe_filename

    try:
        # Save the uploaded document
        document.save(str(document_path))

        # Process the document using the existing pipeline.
        # The pipeline's PDF loader should handle OCR fallback
        # for scanned PDFs.
        result = process_document(str(document_path))

        # Do not report success if the pipeline explicitly
        # reports a failure or creates no usable chunks.
        if result is None or result is False:
            return jsonify({
                "success": False,
                "message": (
                    "Document processing failed. "
                    "No successful processing result was returned."
                )
            }), 500

        if isinstance(result, dict):
            if result.get("success") is False:
                return jsonify({
                    "success": False,
                    "message": result.get(
                        "message",
                        "Document processing failed."
                    ),
                    "result": result
                }), 500

            chunks_created = result.get("chunks_created")

            if chunks_created is not None and chunks_created <= 0:
                return jsonify({
                    "success": False,
                    "message": (
                        "No text chunks were extracted from the document. "
                        "For scanned PDFs, verify that OCR is installed "
                        "and configured correctly."
                    ),
                    "result": result
                }), 422

        return jsonify({
            "success": True,
            "message": (
                "Document processed successfully. "
                "OCR is used by the document-processing pipeline "
                "when required."
            ),
            "result": result
        })

    except Exception:
        app.logger.exception(
            "Document processing failed for %s",
            safe_filename
        )

        return jsonify({
            "success": False,
            "message": (
                "Document processing failed. Check the Flask "
                "server terminal for the detailed error."
            )
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
