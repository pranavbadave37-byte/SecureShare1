from flask import Flask, render_template, request, redirect, session, send_file
import os, random, string, time
import qrcode

app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = "uploads"
QR_FOLDER = "static/qr"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

users = {}
files = {}

def gen_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

def gen_pin():
    return str(random.randint(1000, 9999))

@app.route("/")
def home():
    return render_template("index.html")

# -------- AUTH --------
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        users[request.form["username"]] = request.form["password"]
        return redirect("/login")
    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u in users and users[u] == p:
            session["user"] = u
            return redirect("/")
        return "Invalid credentials"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# -------- UPLOAD --------
@app.route("/upload", methods=["GET","POST"])
def upload():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        file = request.files["file"]
        expiry = int(request.form.get("expiry", 24))

        file_id = gen_id()
        pin = gen_pin()

        path = os.path.join(UPLOAD_FOLDER, file_id)
        file.save(path)

        files[file_id] = {
            "path": path,
            "pin": pin,
            "expiry": time.time() + expiry * 3600
        }

        url = request.host_url + "file/" + file_id

        # QR
        img = qrcode.make(url)
        qr_path = f"{QR_FOLDER}/{file_id}.png"
        img.save(qr_path)

        return render_template("result.html", url=url, pin=pin, qr="/" + qr_path)

    return render_template("upload.html")

# -------- ACCESS FILE --------
@app.route("/file/<file_id>")
def file_access(file_id):
    pin = request.args.get("pin")

    if file_id not in files:
        return "File not found"

    data = files[file_id]

    if time.time() > data["expiry"]:
        return "File expired"

    if pin != data["pin"]:
        return "Wrong PIN"

    return send_file(data["path"], as_attachment=True)

@app.route("/access")
def access_page():
    return render_template("access.html")

if __name__ == "__main__":
    app.run(debug=True)
