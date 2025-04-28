from flask import Flask, request, jsonify, make_response
import pymongo, hashlib, os, pyotp
from datetime import datetime, timedelta
import jwt  
import smtplib
from email.mime.text import MIMEText
app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-123"  

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["authflow_demo"]
EMAIL_CONFIG = {
    'sender': 'datmaster200418@gmail.com',
    'password': 'qwwc bgvf jdte aqax',  
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    
    required_fields = ["username", "password", "fullname", "phone", "email"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Thiếu thông tin bắt buộc"}), 400

    if db.users.find_one({"$or": [{"username": data["username"]}, {"email": data["email"]}]}):
        return jsonify({"error": "Tên đăng nhập hoặc email đã tồn tại"}), 400

    # Tạo OTP
    otp_secret = pyotp.random_base32()
    otp = pyotp.TOTP(otp_secret).now()
    
    # Lưu tạm thông tin
    db.temp_users.insert_one({
        "username": data["username"],
        "password": data["password"],  
        "fullname": data["fullname"],
        "phone": data["phone"],
        "email": data["email"],
        "otp": otp,
        "expires_at": datetime.now() + timedelta(minutes=5)
    })

    # Gửi OTP
    send_otp(data["email"], otp)

    return jsonify({"message": "OTP đã được gửi đến email"}), 200
def send_otp(email, otp):
    try:
        msg = MIMEText(f'Mã OTP của bạn là: {otp}\nMã có hiệu lực trong 5 phút.')
        msg['Subject'] = 'Mã xác thực AuthFlow Demo'
        msg['From'] = EMAIL_CONFIG['sender']
        msg['To'] = email
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'])
            server.send_message(msg)
        print(f"[SUCCESS] Đã gửi OTP đến {email}")
        return True
    except Exception as e:
        print(f"[ERROR] Lỗi gửi email: {str(e)}")
        return False
@app.route("/save-user-info", methods=["POST"])
def save_user_info():
    data = request.get_json()
    email = data.get("email")
    fullname = data.get("fullname")
    phone = data.get("phone")

    if not all([email, fullname, phone]):
        return jsonify({"error": "Thiếu thông tin bắt buộc"}), 400


    db.users.update_one(
        {"email": email},
        {"$set": {"fullname": fullname, "phone": phone}}
    )

    return jsonify({"message": "Cập nhật thông tin thành công"}), 200
# API Đăng nhập
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")  
    password = data.get("password")

    user = db.users.find_one({"username": username})
    if not user:
        return jsonify({"error": "Tên đăng nhập không tồn tại"}), 404

    salt = bytes.fromhex(user["salt"])
    hashed_input = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        100000
    )
    
    if hashed_input.hex() != user["password"]:
        return jsonify({"error": "Mật khẩu không đúng"}), 401
    token = jwt.encode({
        "username": username,  
        "exp": datetime.now() + timedelta(hours=1)
    }, app.config["SECRET_KEY"], algorithm="HS256")

    return jsonify({
        "token": token,
        "username": username  
    }), 200
@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        username = data.get("username")
        otp = data.get("otp")

        if not username or not otp:
            return jsonify({"error": "Thiếu username hoặc OTP"}), 400

        # Kiểm tra OTP trong temp_users
        record = db.temp_users.find_one({
            "username": username,
            "otp": otp,
            "expires_at": {"$gt": datetime.now()}
        })
        
        if not record:
            return jsonify({"error": "OTP không hợp lệ hoặc hết hạn"}), 400

        # Hash password và lưu user
        salt = os.urandom(16)
        hashed_password = hashlib.pbkdf2_hmac(
            "sha256",
            record["password"].encode(),
            salt,
            100000
        )
        
        db.users.insert_one({
            "username": record["username"],
            "password": hashed_password.hex(),
            "salt": salt.hex(),
            "fullname": record["fullname"],
            "phone": record["phone"],
            "email": record["email"]
        })

        # Xóa bản ghi tạm
        db.temp_users.delete_one({"_id": record["_id"]})

        return jsonify({"message": "Xác thực thành công"}), 200

    except Exception as e:
        return jsonify({"error": f"Lỗi server: {str(e)}"}), 500
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    return response
@app.route("/profile", methods=["GET"])
def get_profile():
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        token = token.split(" ")[1]
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        username = payload["username"]
        
        user = db.users.find_one({"username": username}, {"_id": 0, "password": 0, "salt": 0})
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify(user), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401


@app.route("/change-password", methods=["POST"])
def change_password():
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        token = token.split(" ")[1]
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        username = payload["username"]
        data = request.get_json()
        
        user = db.users.find_one({"username": username})
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        salt = bytes.fromhex(user["salt"])
        hashed_input = hashlib.pbkdf2_hmac(
            "sha256",
            data["current_password"].encode(),
            salt,
            100000
        )
        
        if hashed_input.hex() != user["password"]:
            return jsonify({"error": "Current password is incorrect"}), 400
        
        new_salt = os.urandom(16)
        new_hashed_password = hashlib.pbkdf2_hmac(
            "sha256",
            data["new_password"].encode(),
            new_salt,
            100000
        )
        
        db.users.update_one(
            {"username": username},
            {"$set": {
                "password": new_hashed_password.hex(),
                "salt": new_salt.hex()
            }}
        )
        
        return jsonify({"message": "Password changed successfully"}), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
if __name__ == "__main__":
    app.run(port=3000, debug=True)