from flask import Flask, request, jsonify, make_response
import pymongo, hashlib, os, pyotp
from datetime import datetime, timedelta
import jwt  
import smtplib
import random
from email.mime.text import MIMEText
from twilio.rest import Client

app = Flask(__name__)
app.config["SECRET_KEY"] = "Hai_la_s0_1"  

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["authflow_demo"]
EMAIL_CONFIG = {
    'sender': 'datmaster200418@gmail.com',
    'password': 'qwwc bgvf jdte aqax',  
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}

TWILIO_ACCOUNT_SID = "AC9edd7213e48058ec7fd5747cf08530c5"
TWILIO_AUTH_TOKEN = "25a573f24620cc38ae3b456a4c72df89"
TWILIO_VERIFY_SERVICE_SID = "VA34ccf4aa3f2c0365be87d57b7a17d5dd"

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

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
    
    # Lưu tạm thông tin và thêm các trường xác thực
    db.temp_users.insert_one({
        "username": data["username"],
        "password": data["password"],  # Lưu tạm chưa hash
        "fullname": data["fullname"],
        "phone": data["phone"],
        "email": data["email"],
        "cccd": None,
        "cccd_verified": False,  # Thêm trường xác thực CCCD
        "email_verified": False,  # Thêm trường xác thực email
        "phone_verified": False,  # Thêm trường xác thực SĐT
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

        # Hash password và lưu user vào cơ sở dữ liệu chính
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
            "email": record["email"],
            "cccd": None,
            "cccd_verified": False,  # Lưu trạng thái CCCD
            "email_verified": True,  # Lưu trạng thái email
            "phone_verified": False,  # Lưu trạng thái SĐT
        })

        # Xóa bản ghi tạm
        db.temp_users.delete_one({"_id": record["_id"]})

        return jsonify({"message": "Xác thực thành công"}), 200

    except Exception as e:
        return jsonify({"error": f"Lỗi server: {str(e)}"}), 500
    
@app.route("/send-phone-otp", methods=["POST"])
def send_phone_otp():
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        token = token.split(" ")[1]
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        username = payload["username"]

        user = db.users.find_one({"username": username})
        if not user:
            return jsonify({"error": "User not found"}), 404

        phone = user.get("phone")
        if not phone:
            return jsonify({"error": "Chưa có số điện thoại"}), 400

        verification = twilio_client.verify.services(TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=phone,
            channel='sms'
        )

        return jsonify({"message": "OTP đã gửi tới số điện thoại"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/verify-phone-otp", methods=["POST"])
def verify_phone_otp():
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        entered_otp = data.get("otp")

        token = token.split(" ")[1]
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        username = payload["username"]

        user = db.users.find_one({"username": username})
        if not user:
            return jsonify({"error": "User not found"}), 404

        phone = user.get("phone")

        verification_check = twilio_client.verify.services(TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
            to=phone,
            code=entered_otp
        )

        if verification_check.status == "approved":
            db.users.update_one(
                {"username": username},
                {"$set": {"phone_verified": True}}  # Chỉ cập nhật phone_verified
            )
            return jsonify({"message": "Xác nhận số điện thoại thành công!"}), 200
        else:
            return jsonify({"error": "OTP không đúng"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

            
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

        # Thêm trạng thái xác thực vào dữ liệu người dùng
        user["cccd_verified"] = "Đã xác thực" if user.get("cccd_verified") else "Chưa xác thực"
        user["email_verified"] = "Đã xác thực" if user.get("email_verified") else "Chưa xác thực"
        user["phone_verified"] = "Đã xác thực" if user.get("phone_verified") else "Chưa xác thực"

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
    
@app.route("/verify-cccd", methods=["POST"])
def verify_cccd():
    data = request.get_json()
    cccd = data.get("cccd")
    
    if not cccd:
        return jsonify({"error": "Số CCCD không hợp lệ"}), 400
    
    # Kiểm tra token từ header
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Unauthorized, Token missing or invalid"}), 401
    
    try:
        # Lấy token từ "Bearer <token>"
        token = token.split(" ")[1]
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        
        # Lấy username từ payload
        username = payload.get("username")
        
        if not username:
            return jsonify({"error": "Username không có trong token"}), 401
        
        # Kiểm tra CCCD
        validation_result = validate_cccd(cccd)
        if validation_result == "Hợp lệ":
            # Cập nhật vào cơ sở dữ liệu
            db.users.update_one(
                {"username": username},
                {"$set": {
                    "cccd": cccd,  # Lưu số CCCD
                    "cccd_verified": True  # Cập nhật trạng thái CCCD thành đã xác thực
                }}
            )
            return jsonify({"message": "CCCD đã được xác thực!"}), 200
        else:
            return jsonify({"error": validation_result}), 400
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401


@app.route("/generate-share-code", methods=["POST"])
def generate_share_code():
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        token = token.split(" ")[1]
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        username = payload["username"]

        # Tạo mã 6 chữ số
        share_code = f"{random.randint(100000, 999999)}"

        # Lưu vào DB
        db.share_codes.insert_one({
            "username": username,
            "code": share_code,
            "expires_at": datetime.now() + timedelta(minutes=5)
        })

        return jsonify({"share_code": share_code}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/shared-info/<code>", methods=["GET"])
def get_shared_info(code):
    if not code.isdigit() or len(code) != 6:
        return jsonify({"error": "Mã không hợp lệ"}), 400

    record = db.share_codes.find_one({"code": code})
    if not record:
        return jsonify({"error": "Không tìm thấy mã chia sẻ"}), 404

    if datetime.now() > record["expires_at"]:
        return jsonify({"error": "Mã chia sẻ đã hết hạn"}), 410

    username = record["username"]

    user = db.users.find_one(
        {"username": username},
        {
            "_id": 0,
            "username": 1,
            "fullname": 1,
            "email": 1,
            "phone": 1,
            "cccd": 1,
            "cccd_verified": 1,
            "email_verified": 1,
            "phone_verified": 1
        }
    )

    if not user:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404

    # Format trạng thái xác thực
    user["cccd_verified"] = "Đã xác thực" if user.get("cccd_verified") else "Chưa xác thực"
    user["email_verified"] = "Đã xác thực" if user.get("email_verified") else "Chưa xác thực"
    user["phone_verified"] = "Đã xác thực" if user.get("phone_verified") else "Chưa xác thực"

    return jsonify(user), 200



def validate_cccd(cccd):
    # Kiểm tra độ dài số CCCD phải là 12 chữ số
    if len(cccd) != 12 or not cccd.isdigit():
        return "Số CCCD phải gồm 12 chữ số!"
    
    # 1. Kiểm tra mã tỉnh (3 chữ số đầu tiên từ 001 đến 096)
    province_code = int(cccd[:3])
    if not (1 <= province_code <= 96):
        return "Mã tỉnh không hợp lệ!"

    # 2. Kiểm tra mã thế kỷ và giới tính (chữ số thứ 4)
    century_gender = int(cccd[3])
    if century_gender not in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
        return "Mã thế kỷ hoặc giới tính không hợp lệ!"
    
    # 3. Kiểm tra mã năm sinh (2 chữ số tiếp theo)
    birth_year_code = int(cccd[4:6])
    if not (0 <= birth_year_code <= 99):
        return "Mã năm sinh không hợp lệ!"

    # 4. Kiểm tra 6 chữ số cuối (số ngẫu nhiên)
    random_code = cccd[6:]
    if not random_code.isdigit():
        return "Mã ngẫu nhiên không hợp lệ!"
    
    return "Hợp lệ"    
if __name__ == "__main__":
    app.run(port=3000, debug=True)
