import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import pytesseract
import requests
import re

BASE_URL = "http://localhost:3000"
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class AuthFlowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AuthFlow Demo")
        self.root.geometry("500x600")  
        
        self.current_username = ""
        self.password = ""
        self.current_email = ""
        self.current_token = ""
        self.show_main_screen()

    # ------------------------------- Các hàm gọi API ------------------SS----------------------------------------------------------
    def register(self, user_data):
        response = requests.post(
            f"{BASE_URL}/register",
            json=user_data  
        )
        return response.json(), response.status_code

    def send_phone_otp(self):
        """Gửi OTP tới số điện thoại"""
        try:
            response = requests.post(
                f"{BASE_URL}/send-phone-otp",
                headers={"Authorization": f"Bearer {self.current_token}"}
            )
            return response.json(), response.status_code
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}, 500

    def verify_phone_otp(self, otp_code):
        """Xác minh OTP người dùng nhập"""
        try:
            response = requests.post(
                f"{BASE_URL}/verify-phone-otp",
                headers={"Authorization": f"Bearer {self.current_token}"},
                json={"otp": otp_code}
            )
            return response.json(), response.status_code
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}, 500


    def verify_otp(self, otp_data):
            try:
                response = requests.post(
                    f"{BASE_URL}/verify-otp",
                    json=otp_data,
                    timeout=5  
                )
                
                if not response.text:
                    return {"error": "Empty response from server"}, 500
                    
                return response.json(), response.status_code
                
            except requests.exceptions.RequestException as e:
                return {"error": f"Connection error: {str(e)}"}, 500

    def login(self, username, password):  
        response = requests.post(
            f"{BASE_URL}/login",
            json={"username": username, "password": password}  
        )
        return response.json(), response.status_code
    def save_user_info(self, email, fullname, phone):
        """Gọi API lưu thông tin người dùng"""
        response = requests.post(
            f"{BASE_URL}/save-user-info",
            json={"email": email, "fullname": fullname, "phone": phone}
        )
        return response.json(), response.status_code
    def logout(self):
        """Xử lý đăng xuất"""
        self.current_token = ""
        messagebox.showinfo("Thông báo", "Đăng xuất thành công")
        self.show_main_screen()
    

    # ------------------------ Các hàm xử lý giao diện -------------------------------------------------------------------------
    def show_main_screen(self):
        """Màn hình chính với 2 nút Đăng nhập và Đăng ký"""
        self.clear_screen()
        
        tk.Label(self.root, text="Chào mừng đến với AuthFlow Demo", font=("Arial", 14)).pack(pady=20)
        
        tk.Button(
            self.root,
            text="Đăng nhập",
            command=self.show_login_screen,
            width=15,
            height=2
        ).pack(pady=10)
        
        tk.Button(
            self.root,
            text="Đăng ký",
            command=self.show_register_screen,
            width=15,
            height=2
        ).pack(pady=10)

    def show_register_screen(self):
        self.clear_screen()
        
        tk.Label(self.root, text="ĐĂNG KÝ TÀI KHOẢN", font=("Arial", 14)).pack(pady=10)
        
        # Thông tin đăng nhập
        tk.Label(self.root, text="Tên đăng nhập:").pack()
        self.username_entry = tk.Entry(self.root, width=30)
        self.username_entry.pack(pady=5)
        
        tk.Label(self.root, text="Mật khẩu:").pack()
        self.password_entry = tk.Entry(self.root, show="*", width=30)
        self.password_entry.pack(pady=5)
        
        # Thông tin cá nhân
        tk.Label(self.root, text="Họ và tên:").pack()
        self.fullname_entry = tk.Entry(self.root, width=30)
        self.fullname_entry.pack(pady=5)
        
        tk.Label(self.root, text="Số điện thoại:").pack()
        self.phone_entry = tk.Entry(self.root, width=30)
        self.phone_entry.pack(pady=5)
        
        tk.Label(self.root, text="Email:").pack()
        self.email_entry = tk.Entry(self.root, width=30)
        self.email_entry.pack(pady=5)
        
        tk.Button(
            self.root,
            text="Tiếp tục",
            command=self.handle_register,
            width=15
        ).pack(pady=15)
    def show_verify_otp_screen(self):
        self.clear_screen()
        
        tk.Label(self.root, text="XÁC THỰC OTP", font=("Arial", 14)).pack(pady=10)
        tk.Label(self.root, text=f"Mã OTP đã gửi đến {self.current_email}").pack()
        
        tk.Label(self.root, text="Nhập mã OTP:").pack()
        self.otp_entry = tk.Entry(self.root, width=30)
        self.otp_entry.pack(pady=10)
        
        tk.Button(
            self.root,
            text="Xác thực",
            command=self.handle_verify_otp,
            width=15
        ).pack(pady=10)

    def show_login_screen(self):
        self.clear_screen()
        
        tk.Label(self.root, text="ĐĂNG NHẬP", font=("Arial", 12)).pack(pady=10)
        
        tk.Label(self.root, text="Tên đăng nhập:").pack() 
        self.login_username_entry = tk.Entry(self.root, width=30)  
        self.login_username_entry.pack(pady=5)
        
        tk.Label(self.root, text="Mật khẩu:").pack()
        self.login_password_entry = tk.Entry(self.root, show="*", width=30)
        self.login_password_entry.pack(pady=5)
        
        tk.Button(
            self.root,
            text="Đăng nhập",
            command=self.handle_login,
            width=15
        ).pack(pady=10)
        
        tk.Button(
            self.root,
            text="Quay lại",
            command=self.show_main_screen,
            width=10
        ).pack(pady=5)
    
    def show_user_info_screen(self):
        """Màn hình nhập thông tin cá nhân sau khi xác thực OTP"""
        self.clear_screen()
        
        tk.Label(self.root, text="THÔNG TIN CÁ NHÂN", font=("Arial", 12)).pack(pady=10)
        
        tk.Label(self.root, text="Họ và tên:").pack()
        self.fullname_entry = tk.Entry(self.root, width=30)
        self.fullname_entry.pack(pady=5)
        
        tk.Label(self.root, text="Số điện thoại:").pack()
        self.phone_entry = tk.Entry(self.root, width=30)
        self.phone_entry.pack(pady=5)
        
        tk.Button(
            self.root,
            text="Lưu thông tin",
            command=self.handle_save_user_info,
            width=15
        ).pack(pady=10)

    def verify_phone(self):
        """Gọi API xác nhận số điện thoại"""
        try:
            response = requests.post(
                f"{BASE_URL}/verify-phone",
                headers={"Authorization": f"Bearer {self.current_token}"}
            )
            if not response.text:
                return {"error": "Empty response from server"}, 500
            return response.json(), response.status_code
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}, 500


    def show_home_screen(self):
        """Màn hình trang chủ sau khi đăng nhập"""
        self.clear_screen()
        
        tk.Label(self.root, text="TRANG CHỦ", font=("Arial", 16, "bold")).pack(pady=20)
        
        # Nút xem thông tin cá nhân
        tk.Button(
            self.root,
            text="Xem thông tin cá nhân",
            command=self.show_profile_screen,
            width=20,
            height=2
        ).pack(pady=10)
        
        # Nút đổi mật khẩu
        tk.Button(
            self.root,
            text="Đổi mật khẩu",
            command=self.show_change_password_screen,
            width=20,
            height=2
        ).pack(pady=10)
        
        # Nút xác nhận số điện thoại
        tk.Button(
            self.root,
            text="Xác nhận số điện thoại",
            command=self.handle_verify_phone,
            width=20,
            height=2
        ).pack(pady=10)
        
        tk.Button(
            self.root,
            text="Xác nhận CCCD",
            command=self.show_cccd_verification_screen,
            width=20,
            height=2
        ).pack(pady=10)
        
        # Nút đăng xuất
        tk.Button(
            self.root,
            text="Đăng xuất",
            command=self.logout,
            width=20,
            height=2,
            fg="red"
        ).pack(pady=10)

        


    def show_profile_screen(self):
        """Màn hình xem thông tin cá nhân"""
        self.clear_screen()
        
        # Gọi API lấy thông tin user (cần implement endpoint /profile trong server)
        response = requests.get(
            f"{BASE_URL}/profile",
            headers={"Authorization": f"Bearer {self.current_token}"}
        )
        
        if response.status_code == 200:
            user_data = response.json()
            
            tk.Label(self.root, text="THÔNG TIN CÁ NHÂN", font=("Arial", 14)).pack(pady=10)
            
            # Hiển thị thông tin
            info_labels = [
                f"Tên đăng nhập: {user_data.get('username', '')}",
                f"Họ và tên: {user_data.get('fullname', '')}",
                f"Email: {user_data.get('email', '')}",
                f"Số điện thoại: {user_data.get('phone', '')}"
            ]
            
            for label_text in info_labels:
                tk.Label(self.root, text=label_text, font=("Arial", 12)).pack(anchor="w", padx=20, pady=5)
        
        else:
            messagebox.showerror("Lỗi", "Không thể tải thông tin")
        
        tk.Button(
            self.root,
            text="Quay lại",
            command=self.show_home_screen,
            width=15
        ).pack(pady=20)

    def show_change_password_screen(self):
        """Màn hình đổi mật khẩu"""
        self.clear_screen()
        
        tk.Label(self.root, text="ĐỔI MẬT KHẨU", font=("Arial", 14)).pack(pady=10)
        
        tk.Label(self.root, text="Mật khẩu hiện tại:").pack()
        self.current_password_entry = tk.Entry(self.root, show="*", width=30)
        self.current_password_entry.pack(pady=5)
        
        tk.Label(self.root, text="Mật khẩu mới:").pack()
        self.new_password_entry = tk.Entry(self.root, show="*", width=30)
        self.new_password_entry.pack(pady=5)
        
        tk.Label(self.root, text="Nhập lại mật khẩu mới:").pack()
        self.confirm_password_entry = tk.Entry(self.root, show="*", width=30)
        self.confirm_password_entry.pack(pady=5)
        
        tk.Button(
            self.root,
            text="Xác nhận",
            command=self.handle_change_password,
            width=15
        ).pack(pady=10)
        
        tk.Button(
            self.root,
            text="Quay lại",
            command=self.show_home_screen,
            width=10
        ).pack(pady=5)
    
    
    # -------------------------------------Các hàm xử lý sự kiện ---------------------------------------------------------------------------------
    def clear_screen(self):
        """Xóa toàn bộ widget hiện có"""
        for widget in self.root.winfo_children():
            widget.destroy()
    def handle_register(self):
        user_data = {
        "username": self.username_entry.get(),
        "password": self.password_entry.get(),
        "fullname": self.fullname_entry.get(),
        "phone": self.phone_entry.get(),
        "email": self.email_entry.get()
    }
        response, status_code = self.register(user_data)
        self.current_email = user_data["email"]
        if status_code == 200:
            self.current_username = user_data["username"]
            self.show_verify_otp_screen()
        else:
            messagebox.showerror("Lỗi", response.get("error", "Đăng ký thất bại"))

    def handle_verify_otp(self):
        otp_data = {
            "username": self.current_username,
            "otp": self.otp_entry.get()
        }
        
        response, status_code = self.verify_otp(otp_data)
        
        if status_code == 200:
            messagebox.showinfo("Thành công", response.get("message", "Xác thực thành công!"))
            self.show_login_screen()
        else:
            error_msg = response.get("error", "Xác thực thất bại")
            messagebox.showerror("Lỗi", error_msg)
    def handle_save_user_info(self):
        """Xử lý lưu thông tin cá nhân"""
        fullname = self.fullname_entry.get()
        phone = self.phone_entry.get()

        if not fullname or not phone:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin")
            return

        response, status_code = self.save_user_info(self.email, fullname, phone)
        if status_code == 200:
            messagebox.showinfo("Thành công", "Đăng ký hoàn tất!")
            self.show_login_screen()
        else:
            messagebox.showerror("Lỗi", response.get("error", "Lỗi khi lưu thông tin"))
    def handle_login(self):
        """Sửa lại hàm xử lý đăng nhập"""
        username = self.login_username_entry.get()
        password = self.login_password_entry.get()
        
        response, status_code = self.login(username, password)
        if status_code == 200:
            self.current_token = response["token"]  
            messagebox.showinfo("Thành công", "Đăng nhập thành công!")
            self.show_home_screen()  
        else:
            messagebox.showerror("Lỗi", response.get("error", "Đăng nhập thất bại"))
    def handle_change_password(self):
        """Xử lý đổi mật khẩu"""
        current_pass = self.current_password_entry.get()
        new_pass = self.new_password_entry.get()
        confirm_pass = self.confirm_password_entry.get()
        
        if new_pass != confirm_pass:
            messagebox.showerror("Lỗi", "Mật khẩu mới không khớp")
            return
        response = requests.post(
            f"{BASE_URL}/change-password",
            headers={"Authorization": f"Bearer {self.current_token}"},
            json={
                "current_password": current_pass,
                "new_password": new_pass
            }
        )
        
        if response.status_code == 200:
            messagebox.showinfo("Thành công", "Đổi mật khẩu thành công")
            self.show_home_screen()
        else:
            messagebox.showerror("Lỗi", response.json().get("error", "Đổi mật khẩu thất bại"))

    def handle_verify_phone(self):
        """Xử lý xác nhận số điện thoại qua OTP"""
        send_response, send_status = self.send_phone_otp()
        if send_status != 200:
            messagebox.showerror("Lỗi", send_response.get("error", "Không thể gửi OTP"))
            return

        # Mở cửa sổ nhập OTP
        otp_window = tk.Toplevel(self.root)
        otp_window.title("Nhập mã OTP")
        otp_window.geometry("300x150")

        tk.Label(otp_window, text="Nhập mã OTP (6 số):").pack(pady=10)
        otp_entry = tk.Entry(otp_window, width=20)
        otp_entry.pack(pady=5)

        def submit_otp():
            otp_code = otp_entry.get()
            verify_response, verify_status = self.verify_phone_otp(otp_code)
            if verify_status == 200:
                messagebox.showinfo("Thành công", verify_response.get("message", "Xác nhận số điện thoại thành công"))
                otp_window.destroy()
            else:
                messagebox.showerror("Lỗi", verify_response.get("error", "OTP sai. Vui lòng nhập lại."))

        tk.Button(otp_window, text="Xác thực", command=submit_otp).pack(pady=10)

    def show_cccd_verification_screen(self):
        """Màn hình tải ảnh và xác nhận CCCD"""
        self.clear_screen()
        
        tk.Label(self.root, text="Xác thực CCCD", font=("Arial", 14)).pack(pady=10)
        
        # Nút để chọn ảnh CCCD
        tk.Button(
            self.root,
            text="Chọn ảnh CCCD",
            command=self.upload_cccd_image,
            width=20,
            height=2
        ).pack(pady=20)

        tk.Button(
            self.root,
            text="Quay lại",
            command=self.show_home_screen,
            width=20,
            height=2
        ).pack(pady=10)

    def upload_cccd_image(self):
        """Cho phép người dùng chọn ảnh và thực hiện xác thực"""
        # Mở cửa sổ để người dùng chọn ảnh
        file_path = filedialog.askopenfilename(title="Chọn ảnh CCCD", filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        
        if file_path:
            # Trích xuất văn bản từ ảnh bằng OCR
            cccd = self.extract_cccd_from_image(file_path)
            
            if cccd:
                # Kiểm tra tính hợp lệ của CCCD
                validation_result = self.validate_cccd(cccd)
                
                if validation_result == "Hợp lệ":
                    messagebox.showinfo("Thành công", "CCCD hợp lệ!")
                else:
                    messagebox.showerror("Lỗi", validation_result)  # Thông báo lý do không hợp lệ
            else:
                messagebox.showerror("Lỗi", "Không thể trích xuất CCCD từ ảnh.")

    def extract_cccd_from_image(self, image_path):
        """Trích xuất số CCCD từ ảnh sử dụng OCR"""
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        
        # Sử dụng regex để tìm số CCCD trong văn bản
        match = re.search(r'\d{12}', text)
        
        if match:
            return match.group(0)
        else:
            return None

    def validate_cccd(self, cccd):
        """Kiểm tra tính hợp lệ của CCCD dựa trên quy định"""
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
        
        return "Hợp lệ"  # Nếu tất cả các phần hợp lệ

    def verify_cccd(self, cccd):
        """Gọi API xác thực CCCD"""
        response = requests.post(
            f"{BASE_URL}/verify-cccd", 
            json={"cccd": cccd}
        )
        
        if response.status_code == 200:
            messagebox.showinfo("Thành công", "CCCD hợp lệ!")
            self.show_main_screen()
        else:
            messagebox.showerror("Lỗi", response.json().get("error", "Không hợp lệ"))

    def clear_screen(self):
        """Xóa toàn bộ widget hiện có"""
        for widget in self.root.winfo_children():
            widget.destroy()



if __name__ == "__main__":
    root = tk.Tk()
    app = AuthFlowApp(root)
    root.mainloop()
