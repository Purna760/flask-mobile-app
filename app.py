from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Home page (frontend)
@app.route("/")
def index():
    return render_template("index.html")

# Example backend API: adds two numbers
@app.route("/api/add", methods=["POST"])
def add_numbers():
    data = request.get_json() or {}
    try:
        a = float(data.get("a", 0))
        b = float(data.get("b", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid numbers"}), 400

    return jsonify({"result": a + b})

if __name__ == "__main__":
    # This is used only if you run it directly (Render will use gunicorn)
    app.run(host="0.0.0.0", port=5000)
  
