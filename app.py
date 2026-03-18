from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import bcrypt
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "khoa_bi_mat_123")  # dùng để mã hóa session

# ============ DATABASE ============
def get_db():
    thu_muc = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(os.path.join(thu_muc, "auth.db"))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    # Bảng users
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mat_khau TEXT NOT NULL
        )
    """)
    # Bảng todo — có thêm user_id để biết của ai
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cong_viec (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten TEXT NOT NULL,
            hoan_thanh INTEGER DEFAULT 0,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

# ============ HELPER ============
def dang_nhap_roi():
    """Kiểm tra user đã đăng nhập chưa"""
    return "user_id" in session

# ============ ROUTES ============
@app.route("/")
def trang_chu():
    if not dang_nhap_roi():
        return redirect(url_for("dang_nhap"))
    conn = get_db()
    viec_list = conn.execute(
        "SELECT * FROM cong_viec WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return render_template("index.html", viec_list=viec_list, ten=session["ten"])

@app.route("/dang-ky", methods=["GET", "POST"])
def dang_ky():
    if request.method == "POST":
        ten = request.form["ten"]
        email = request.form["email"]
        mat_khau = request.form["mat_khau"]

        # Hash mật khẩu — không lưu mật khẩu thật!
        mat_khau_hash = bcrypt.hashpw(mat_khau.encode("utf-8"), bcrypt.gensalt())

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users (ten, email, mat_khau) VALUES (?, ?, ?)",
                (ten, email, mat_khau_hash)
            )
            conn.commit()
            conn.close()
            flash("Đăng ký thành công! Hãy đăng nhập.", "success")
            return redirect(url_for("dang_nhap"))
        except:
            flash("Email đã tồn tại!", "error")

    return render_template("dangky.html")

@app.route("/dang-nhap", methods=["GET", "POST"])
def dang_nhap():
    if request.method == "POST":
        email = request.form["email"]
        mat_khau = request.form["mat_khau"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        # Kiểm tra email và mật khẩu
        if user and bcrypt.checkpw(mat_khau.encode("utf-8"), user["mat_khau"]):
            session["user_id"] = user["id"]
            session["ten"] = user["ten"]
            return redirect(url_for("trang_chu"))
        else:
            flash("Email hoặc mật khẩu sai!", "error")

    return render_template("dangnhap.html")

@app.route("/dang-xuat")
def dang_xuat():
    session.clear()  # xóa toàn bộ session
    return redirect(url_for("dang_nhap"))

@app.route("/them", methods=["POST"])
def them():
    if not dang_nhap_roi():
        return redirect(url_for("dang_nhap"))
    ten = request.form["ten"]
    if ten.strip():
        conn = get_db()
        conn.execute(
            "INSERT INTO cong_viec (ten, user_id) VALUES (?, ?)",
            (ten, session["user_id"])  # lưu kèm user_id
        )
        conn.commit()
        conn.close()
    return redirect(url_for("trang_chu"))

@app.route("/xoa/<int:id>")
def xoa(id):
    if not dang_nhap_roi():
        return redirect(url_for("dang_nhap"))
    conn = get_db()
    # Xóa đúng việc của đúng user — tránh user A xóa việc của user B!
    conn.execute(
        "DELETE FROM cong_viec WHERE id = ? AND user_id = ?",
        (id, session["user_id"])
    )
    conn.commit()
    conn.close()
    return redirect(url_for("trang_chu"))

init_db()
if __name__ == "__main__":
    
    app.run(debug=True)