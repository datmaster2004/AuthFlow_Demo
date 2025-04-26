import tkinter as tk
from tkinter import messagebox
import requests

BASE_URL = "http://localhost:3000"

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

    # ------------------------------- Các hàm gọi API ----------------------------------------------------------------------------
    def register(self, user_data):
        response = requests.post(
            f"{BASE_URL}/register",
            json=user_data  
        )
        return response.json(), response.status_code

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

    def show_home_screen(self):
        """Màn hình trang chủ sau khi đăng nhập"""
        self.clear_screen()
        
        tk.Label(self.root, text="TRANG CHỦ", font=("Arial", 16, "bold")).pack(pady=20)
        
        # Nút xem thông tin
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
if __name__ == "__main__":
    root = tk.Tk()
    app = AuthFlowApp(root)
    root.mainloop()