"""
自动提交订单工具（猴发卡网 → 支付宝支付二维码）

依赖库:
    requests
    beautifulsoup4
    qrcode[pil]
    Pillow

使用方法:
    pip install -r requirements.txt
    python auto_order.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import re
import random
import os
import tempfile
import subprocess
import warnings
import base64
import json
import pickle
from collections import OrderedDict
from datetime import datetime
from urllib.parse import urlencode, urlparse
from io import BytesIO

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
import qrcode
from PIL import Image, ImageTk

# 导入登录和商品修改模块
from login_4yuns import login_to_4yuns, get_goods_edit_data, modify_goods_price

# 禁用 SSL 验证警告
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# 强制禁用SSL验证（解决打包后SSL证书问题）
import os
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''


class AutoOrderApp:
    """自动提交订单工具主类"""

    def __init__(self, root):
        self.root = root
        self.root.title("四云发卡")
        self.root.geometry("550x750")
        self.root.resizable(True, True)

        # HTTP 会话（关闭 SSL 验证以支持自签名证书）
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        # 线程和队列
        self.worker_thread = None
        self.log_queue = queue.Queue()
        self.current_qr_image = None  # 保存当前二维码的 PIL Image 对象

        # 当前商品ID（用于改价）
        self.current_goods_id = None
        
        # 平台配置（默认猴发卡）
        self.platform_host = "https://shop.4yuns.com"
        
        # 平台目录（每个平台独立的配置存放在这里）
        self.platforms_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "platforms")
        if not os.path.exists(self.platforms_dir):
            os.makedirs(self.platforms_dir)

        # 持久化 s1c9ae71b Cookie（首次获取后复用）
        self.saved_s1c9ae71b = None

        # 商户登录会话（登录后保存）
        self.merchant_session = None
        self.merchant_logged_in = False
        self.merchant_username = ""

        # 保存原始窗口标题
        self.original_title = self.root.title()

        # Cookie 持久化文件路径
        self.cookie_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merchant_cookies_4yuns.pkl")
        
        # 商品链接持久化文件路径
        self.url_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "url_config_4yuns.pkl")
        
        # 登录凭证持久化文件路径
        self.credentials_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login_credentials_4yuns.pkl")

        # 启动时加载已保存的 Cookie
        self._load_merchant_cookies()
        
        # 启动时加载商品链接
        self._load_url_config()
        
        # 启动时加载登录凭证
        self._load_credentials()

        # 定时检查日志队列
        self.root.after(100, self._process_log_queue)

        self._setup_ui()

    def _setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)


        # 1. 商品链接输入
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(url_frame, text="商品链接:").pack(side=tk.LEFT, padx=(0, 5))
        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 1.5. 改价功能
        price_frame = ttk.LabelFrame(main_frame, text="商品改价", padding="5")
        price_frame.pack(fill=tk.X, pady=(0, 10))

        # 当前价格显示
        price_inner_frame = ttk.Frame(price_frame)
        price_inner_frame.pack(fill=tk.X)

        ttk.Label(price_inner_frame, text="当前价格:").pack(side=tk.LEFT, padx=(0, 5))
        self.current_price_label = ttk.Label(price_inner_frame, text="未加载", foreground="gray")
        self.current_price_label.pack(side=tk.LEFT, padx=(0, 20))

        # 新价格输入
        ttk.Label(price_inner_frame, text="新价格:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_price_entry = ttk.Entry(price_inner_frame, width=15)
        self.new_price_entry.pack(side=tk.LEFT, padx=(0, 10))

        # 获取价格按钮
        self.get_price_btn = ttk.Button(
            price_inner_frame,
            text="获取商品价格",
            command=self._on_get_price
        )
        self.get_price_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 修改按钮
        self.modify_price_btn = ttk.Button(
            price_inner_frame,
            text="修改价格",
            command=self._on_modify_price,
            state=tk.DISABLED
        )
        self.modify_price_btn.pack(side=tk.LEFT)

        # 2. 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.login_btn = ttk.Button(
            btn_frame, text="登录店铺", command=self._on_login
        )
        self.login_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 启动时更新登录按钮状态
        self.root.after(200, self._update_login_button)

        self.submit_btn = ttk.Button(
            btn_frame, text="获取支付二维码", command=self._on_submit
        )
        self.submit_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.clear_btn = ttk.Button(
            btn_frame, text="清空", command=self._on_clear
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.copy_btn = ttk.Button(
            btn_frame, text="复制二维码", command=self._on_copy_qr, state=tk.DISABLED
        )
        self.copy_btn.pack(side=tk.LEFT)

        # 3. 二维码展示区
        qr_frame = ttk.LabelFrame(main_frame, text="支付二维码", padding="5")
        qr_frame.pack(fill=tk.X, pady=(0, 10))

        self.qr_label = tk.Label(
            qr_frame,
            text="二维码将显示在此处",
            bg="#f0f0f0",
            relief=tk.SUNKEN,
            anchor="center"
        )
        self.qr_label.pack(fill=tk.X, pady=5)

        # 4. 日志输出框
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            width=60,
            height=12,
            state=tk.DISABLED,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)




    def _log(self, message):
        """线程安全地添加日志到队列"""
        self.log_queue.put(message)

    def _process_log_queue(self):
        """处理日志队列，更新 UI"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        self.root.after(100, self._process_log_queue)

    def _on_submit(self):
        """点击获取支付二维码按钮"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入商品链接")
            return

        # 清空日志框
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        # 禁用按钮，启用清空，禁用复制
        self.submit_btn.config(state=tk.DISABLED)
        self.copy_btn.config(state=tk.DISABLED)
        self.current_qr_image = None

        # 启动工作线程
        self.worker_thread = threading.Thread(
            target=self._worker, args=(url,), daemon=True
        )
        self.worker_thread.start()

    def _on_clear(self):
        """点击清空按钮"""
        self.url_entry.delete(0, tk.END)
        self.qr_label.config(image="", text="二维码将显示在此处")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.copy_btn.config(state=tk.DISABLED)
        self.current_qr_image = None
        # 重置改价相关UI
        self.current_price_label.config(text="未加载", foreground="gray")
        self.new_price_entry.delete(0, tk.END)
        self.modify_price_btn.config(state=tk.DISABLED)
        self.get_price_btn.config(state=tk.NORMAL)
        self.current_goods_id = None

    def _on_get_price(self):
        """点击获取商品价格按钮"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("提示", "请先输入商品链接")
            return
        
        # 检查是否已登录
        if not self.merchant_logged_in or not self.merchant_session:
            messagebox.showwarning("提示", "请先登录店铺")
            return
        
        # 禁用按钮
        self.get_price_btn.config(state=tk.DISABLED, text="获取中...")
        
        # 在新线程中获取价格
        def get_price_thread():
            try:
                # 从商品页面获取参数（使用商户Session）
                parsed = urlparse(url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                path = parsed.path
                
                request_url = f"{base_url}{path}"
                
                # 输出完整请求日志
                # self._log(f"获取价格 - 请求URL: {request_url}")
                # self._log(f"获取价格 - 请求头: {dict(self.merchant_session.headers)}")
                # self._log(f"获取价格 - Cookie: {dict(self.merchant_session.cookies)}")
                # self._log(f"获取价格 - verify: {self.merchant_session.verify}")
                
                # 临时修改Accept头为HTML（避免服务器返回JSON编码的HTML）
                original_accept = self.merchant_session.headers.get("Accept", "")
                self.merchant_session.headers.update({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Dest": "document",
                })
                
                resp = self.merchant_session.get(request_url, timeout=15)
                
                # 恢复原始请求头
                self.merchant_session.headers.update({
                    "Accept": original_accept,
                })
                
                # 输出完整响应日志
                # self._log(f"获取价格 - 响应状态码: {resp.status_code}")
                # self._log(f"获取价格 - 响应头: {dict(resp.headers)}")
                # self._log(f"获取价格 - 响应体: {resp.text}")
                
                if resp.status_code != 200:
                    raise Exception(f"请求失败: HTTP {resp.status_code}")
                
                # 处理转义的HTML（反转义 \/ 和 \n 等）
                html_content = resp.text
                html_content = html_content.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
                
                soup = BeautifulSoup(html_content, "html.parser")
                
                def get_input_value(name):
                    inp = soup.find("input", {"name": name})
                    return inp.get("value", "") if inp else ""
                
                goodid = get_input_value("goodid")
                if not goodid:
                    raise Exception("未找到商品ID")
                
                # 提取价格（从 span.card__detail_price）
                price_span = soup.find("span", class_="card__detail_price")
                if not price_span:
                    raise Exception("未找到商品价格")
                
                # 提取价格文本（如 "￥50.00"），去除￥符号
                price_text = price_span.get_text().strip()
                price = price_text.replace("￥", "").replace("¥", "")
                
                if not price:
                    raise Exception("价格提取为空")
                
                # 保存商品ID
                self.current_goods_id = goodid
                
                # 保存商品链接
                self._save_url_config(url)
                
                # 更新UI
                self.root.after(0, lambda p=price: self.current_price_label.config(text=f"¥{p}", foreground="blue"))
                self.root.after(0, lambda: self.modify_price_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.get_price_btn.config(state=tk.NORMAL, text="获取商品价格"))
                self.root.after(0, lambda: self._log(f"成功: 获取商品价格 ¥{price}, 商品ID: {goodid}"))
                
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self._log(f"错误: 获取商品价格失败 - {error_msg}"))
                self.root.after(0, lambda: messagebox.showerror("错误", f"获取商品价格失败:\n{error_msg}"))
                self.root.after(0, lambda: self.get_price_btn.config(state=tk.NORMAL, text="获取商品价格"))
        
        threading.Thread(target=get_price_thread, daemon=True).start()

    def _on_modify_price(self):
        """点击修改价格按钮"""
        # 检查是否已登录（最先判断）
        if not self.merchant_logged_in or not self.merchant_session:
            messagebox.showwarning("提示", "请先登录店铺")
            return
        
        # 检查商品ID是否存在
        if not self.current_goods_id:
            messagebox.showwarning("提示", "请先点击'获取商品价格'按钮")
            return
        
        new_price = self.new_price_entry.get().strip()
        if not new_price:
            messagebox.showwarning("提示", "请输入新价格")
            return
        
        # 验证价格格式
        try:
            price_val = float(new_price)
            if price_val <= 0:
                raise ValueError("价格必须大于0")
        except ValueError as e:
            messagebox.showwarning("提示", f"价格格式错误: {e}")
            return
        
        # 禁用按钮
        self.modify_price_btn.config(state=tk.DISABLED, text="修改中...")
        
        # 在新线程中执行改价
        def modify_thread():
            try:
                # 首先获取商品编辑数据
                self._log(f"正在获取商品信息...")
                goods_data = get_goods_edit_data(self.merchant_session, goods_id=self.current_goods_id)
                
                # 修改价格
                self._log(f"正在修改价格为 {new_price}...")
                result = modify_goods_price(
                    self.merchant_session,
                    goods_id=self.current_goods_id,
                    new_price=new_price,
                    goods_data=goods_data
                )
                
                self._log(f"成功: 价格已修改为 ¥{new_price}")
                # 成功后自动更新价格标签
                self.root.after(0, lambda: self.current_price_label.config(text=f"¥{new_price}", foreground="green"))
                self.root.after(0, lambda: self.modify_price_btn.config(state=tk.NORMAL, text="修改价格"))
                
            except Exception as e:
                error_msg = str(e)
                self._log(f"错误: 修改价格失败 - {error_msg}")
                self.root.after(0, lambda: self.modify_price_btn.config(state=tk.NORMAL, text="修改价格"))
        
        threading.Thread(target=modify_thread, daemon=True).start()

    def _on_copy_qr(self):
        """点击复制二维码按钮"""
        if self.current_qr_image is None:
            messagebox.showwarning("提示", "暂无二维码可复制")
            return

        try:
            # 保存为临时文件
            temp_path = os.path.join(tempfile.gettempdir(), "qrcode_clipboard.png")
            self.current_qr_image.save(temp_path, "PNG")

            # Windows: 使用 PowerShell 复制到剪贴板
            if os.name == "nt":
                ps_script = (
                    'Add-Type -AssemblyName System.Windows.Forms; '
                    '$img = [System.Drawing.Image]::FromFile("' + temp_path + '"); '
                    '[System.Windows.Forms.Clipboard]::SetImage($img); '
                    '$img.Dispose()'
                )
                subprocess.run(
                    ["powershell", "-command", ps_script],
                    check=True,
                    capture_output=True,
                    timeout=10
                )
            else:
                messagebox.showinfo("提示", "当前仅支持 Windows 系统复制图片到剪贴板")
                return

            self._log("成功: 二维码图片已复制到剪贴板")
        except Exception as e:
            self._log(f"错误: 复制二维码失败 - {e}")
            messagebox.showerror("错误", f"复制二维码失败:\n{e}")

    def _update_login_button(self):
        """更新登录按钮状态"""
        if self.merchant_logged_in:
            # 已登录：显示用户名，设置样式
            display_name = self.merchant_username[:15] + "..." if len(self.merchant_username) > 15 else self.merchant_username
            
            # 配置成功样式（绿色文字）
            style = ttk.Style()
            style.configure("Success.TButton", foreground="#006400", font=("", 9, "bold"))
            
            self.login_btn.config(
                text=f"✓ {display_name}",
                style="Success.TButton"
            )
            
            # 更新窗口标题（在原始标题后添加用户名）
            self.root.title(f"{self.original_title} - {self.merchant_username}")
        else:
            # 未登录：显示默认文本
            self.login_btn.config(text="登录店铺", style="TButton")
            
            # 恢复原始窗口标题
            self.root.title(self.original_title)

    def _on_login(self):
        """点击登录店铺按钮"""
        # 创建登录对话框
        login_window = tk.Toplevel(self.root)
        login_window.title("商户登录")
        login_window.geometry("350x280")
        login_window.resizable(False, False)
        login_window.transient(self.root)
        login_window.grab_set()

        # 居中显示
        login_window.update_idletasks()
        x = (login_window.winfo_screenwidth() // 2) - (350 // 2)
        y = (login_window.winfo_screenheight() // 2) - (280 // 2)
        login_window.geometry(f"+{x}+{y}")

        # 主框架
        main_frame = ttk.Frame(login_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 如果已登录，显示已登录状态
        if self.merchant_logged_in:
            status_frame = ttk.Frame(main_frame)
            status_frame.pack(fill=tk.X, pady=(0, 15))

            ttk.Label(status_frame, text="当前已登录:", font=("", 10, "bold")).pack(side=tk.LEFT)
            ttk.Label(status_frame, text=f"✓ {self.merchant_username}", foreground="green", font=("", 10, "bold")).pack(side=tk.LEFT, padx=(5, 0))

            # 重新登录按钮 - 清除登录状态并显示登录表单
            def do_relogin():
                # 清除登录状态
                self.merchant_session = None
                self.merchant_logged_in = False
                self.merchant_username = ""
                
                # 删除 Cookie 文件
                if os.path.exists(self.cookie_file):
                    try:
                        os.remove(self.cookie_file)
                        self._log("提示: 已清除保存的登录状态")
                    except Exception as e:
                        self._log(f"提示: 清除 Cookie 文件失败 - {e}")
                
                # 更新主窗口按钮
                self._update_login_button()
                
                # 销毁当前窗口，重新打开登录窗口
                login_window.destroy()
                self._on_login()

            ttk.Button(main_frame, text="重新登录", command=do_relogin).pack(fill=tk.X, pady=(10, 0))

            # 关闭按钮
            ttk.Button(main_frame, text="关闭", command=login_window.destroy).pack(fill=tk.X, pady=(5, 0))
            return

        # 用户名
        ttk.Label(main_frame, text="用户名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        username_entry = ttk.Entry(main_frame, width=30)
        username_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # 密码
        ttk.Label(main_frame, text="密码:").grid(row=1, column=0, sticky=tk.W, pady=5)
        password_entry = ttk.Entry(main_frame, width=30, show="*")
        password_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # 加载当前平台的登录凭证
        saved_username = getattr(self, '_login_username', '')
        saved_password = getattr(self, '_login_password', '')
        
        # 如果没有平台凭证，尝试加载全局凭证
        if not saved_username or not saved_password:
            global_username, global_password = self._load_credentials()
            if global_username:
                saved_username = global_username
            if global_password:
                saved_password = global_password
        
        if saved_username:
            username_entry.insert(0, saved_username)
        else:
            username_entry.insert(0, "yousha01")  # 默认值
        
        if saved_password:
            password_entry.insert(0, saved_password)
        else:
            password_entry.insert(0, "Suorona258")  # 默认值

        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)

        def do_login():
            username = username_entry.get().strip()
            password = password_entry.get().strip()

            if not username or not password:
                messagebox.showwarning("提示", "请输入用户名和密码")
                return

            # 禁用按钮
            login_btn.config(state=tk.DISABLED, text="登录中...")
            login_window.update()

            # 在新线程中执行登录
            def login_thread():
                try:
                    # 使用当前平台的 host 进行登录
                    session, cookies = login_to_4yuns(username, password, base_url=self.platform_host)
                    self.merchant_session = session
                    self.merchant_logged_in = True
                    self.merchant_username = username
                    
                    # 保存当前平台的登录凭证
                    self._login_username = username
                    self._login_password = password

                    # 从登录 Cookie 中提取 s1c9ae71b
                    for cookie in session.cookies:
                        if 's1c9ae71b' in cookie.name.lower():
                            self.saved_s1c9ae71b = cookie.value
                            self._log(f"成功: 从登录响应中提取 s1c9ae71b Cookie: {self.saved_s1c9ae71b[:10]}...")
                            break

                    # 保存 Cookie 到文件（全局持久化，用于启动时恢复）
                    self._save_merchant_cookies(username)
                    
                    # 保存登录凭证到全局（用于首次使用时恢复）
                    self._save_credentials(username, password)
                    

                    self._log(f"成功: 商户登录成功，用户: {username}")
                    self.root.after(0, lambda: self._update_login_button())
                    self.root.after(0, login_window.destroy)
                except Exception as e:
                    error_msg = str(e)
                    self._log(f"错误: 商户登录失败 - {error_msg}")
                    self.root.after(0, lambda: messagebox.showerror("错误", f"登录失败:\n{error_msg}"))
                    self.root.after(0, lambda: login_btn.config(state=tk.NORMAL, text="登录"))

            threading.Thread(target=login_thread, daemon=True).start()

        login_btn = ttk.Button(btn_frame, text="登录", command=do_login)
        login_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttk.Button(btn_frame, text="取消", command=login_window.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # 回车键登录
        password_entry.bind("<Return>", lambda e: do_login())

    def _worker(self, url):
        """工作线程：执行完整的6步流程"""
        try:
            # 检查是否已登录商户后台
            if not self.merchant_logged_in or not self.merchant_session:
                raise Exception("请先登录店铺")

            # 步骤1: 从商品页面获取参数（使用商户Session中的Cookie）
            self._log("步骤1: 获取 Cookie 及商品参数...")
            cookie, params = self._step1_get_cookie_and_params(url)
            goodid = params['goodid']
            current_price = params.get('price', '0.00')
            self._log(f"成功: 获取 Cookie: {cookie[:10]}..., 商品ID: {goodid}, 当前价格: ¥{current_price}")

            # 保存商品ID并更新UI显示
            self.current_goods_id = goodid
            self.root.after(0, lambda: self.modify_price_btn.config(state=tk.NORMAL))

            # 步骤2
            self._log("步骤2: 提交订单，获取 orderid...")
            orderid = self._step2_submit_order(cookie, params)
            self._log(f"成功: 订单ID: {orderid}")

            # 步骤2.5: 调用check_buyer验证指纹（四云发卡需要）
            self._log("步骤2.5: 验证买家指纹...")
            self._step25_check_buyer(orderid)
            
            # 步骤3
            self._log("步骤3: 获取支付宝支付表单...")
            step3_result = self._step3_get_alipay_form(cookie, orderid)
            
            # 步骤3.5: 如果是重定向地址，请求获取支付宝表单
            if isinstance(step3_result, dict) and "redirect_url" in step3_result:
                self._log("步骤3.5: 请求重定向地址，获取支付宝表单...")
                alipay_params = self._step35_get_alipay_form_from_redirect(step3_result["redirect_url"], cookie)
            else:
                # 兼容猴发卡：直接返回表单参数
                alipay_params = step3_result
            
            self._log(f"成功: 获取支付宝表单参数 ({len(alipay_params)} 个)")

            # 步骤4
            self._log("步骤4: 请求支付宝网关，获取重定向地址...")
            location1, alipay_cookies = self._step4_request_alipay_gateway(alipay_params)
            self._log(f"成功: 获取第一次重定向地址")

            # 步骤5
            self._log("步骤5: 跟随重定向，获取最终支付链接...")
            cashier_url = self._step5_follow_redirect(location1, alipay_cookies)
            self._log(f"成功: 获取收银台链接")

            # 步骤6
            self._log("步骤6: 生成二维码...")
            self._step6_generate_qrcode(cashier_url)
            self._log("成功: 二维码已生成并显示")

            # 启用复制按钮
            self.root.after(0, lambda: self.copy_btn.config(state=tk.NORMAL))

        except Exception as e:
            error_msg = str(e)
            self._log(f"错误: {error_msg}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"操作失败:\n{error_msg}"))
        finally:
            self.root.after(0, lambda: self.submit_btn.config(state=tk.NORMAL))

    def _step1_get_cookie_and_params(self, url):
        """步骤1: 获取 Cookie 及商品参数"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path

        resp = self.session.get(f"{base_url}{path}", timeout=15)
        if resp.status_code != 200:
            raise Exception(f"步骤1请求失败: HTTP {resp.status_code}")

        # 提取 s1c9ae71b cookie
        cookie_value = None

        # 优先使用已保存的 Cookie
        if self.saved_s1c9ae71b:
            cookie_value = self.saved_s1c9ae71b
            self._log(f"复用已保存的 s1c9ae71b Cookie: {cookie_value[:10]}...")
        else:
            # 首次获取，从响应中提取
            for cookie_name, cookie_val in resp.cookies.items():
                if "s1c9ae71b" in cookie_name.lower():
                    cookie_value = cookie_val
                    break

            if not cookie_value:
                # 尝试从 set-cookie 头中直接提取
                set_cookies = resp.headers.get("set-cookie", "")
                match = re.search(r's1c9ae71b=([^;]+)', set_cookies, re.IGNORECASE)
                if match:
                    cookie_value = match.group(1)
                else:
                    raise Exception("步骤1: 未找到 s1c9ae71b Cookie")

            # 保存 Cookie 供后续复用
            self.saved_s1c9ae71b = cookie_value
            self._log(f"首次获取并保存 s1c9ae71b Cookie: {cookie_value[:10]}...")

        # 清除session中所有Cookie，只设置s1c9ae71b
        self.session.cookies.clear()
        self.session.cookies.set("s1c9ae71b", cookie_value)
        self._log(f"步骤1: 清除多余Cookie，只保留 s1c9ae71b={cookie_value[:10]}...")

        # 解析 HTML
        soup = BeautifulSoup(resp.text, "html.parser")

        # 提取隐藏字段
        def get_input_value(name):
            inp = soup.find("input", {"name": name})
            return inp.get("value", "") if inp else ""

        goodid = get_input_value("goodid")
        userid = get_input_value("userid")
        token = get_input_value("token")
        cateid = get_input_value("cateid")
        price = get_input_value("price")
        danjia = get_input_value("danjia")
        kucun = get_input_value("kucun")
        feePayer = get_input_value("feePayer")
        fee_rate = get_input_value("fee_rate")
        min_fee = get_input_value("min_fee")
        rate = get_input_value("rate")

        if not all([goodid, userid, token]):
            raise Exception("步骤1: 商品页面解析失败，缺少必要参数 (goodid/userid/token)")

        params = {
            "goodid": goodid,
            "userid": userid,
            "token": token,
            "cateid": cateid,
            "price": price,
            "danjia": danjia,
            "kucun": kucun,
            "feePayer": feePayer if feePayer else "2",
            "fee_rate": fee_rate if fee_rate else "0.05",
            "min_fee": min_fee if min_fee else "0.1",
            "rate": rate if rate else "100",
            "is_contact_limit": "default",
            "limit_quantity": "1",
            "cardNoLength": "0",
            "cardPwdLength": "0",
            "is_discount": "0",
            "coupon_ctype": "0",
            "coupon_value": "0",
            "sms_price": "0",
            "is_pwdforsearch": "",
            "is_coupon": "",
            "select_cards": "",
        }

        return cookie_value, params

    def _step2_submit_order(self, cookie, params):
        """步骤2: 提交订单，获取 orderid"""
        # 生成随机手机号
        contact = f"1{random.randint(3,9)}{''.join([str(random.randint(0,9)) for _ in range(9)])}"

        # 计算 paymoney: price * quantity * (1 + fee_rate)
        quantity = 1
        price_val = float(params["price"]) if params["price"] else float(params["danjia"])
        fee_rate_val = float(params["fee_rate"])
        paymoney = round(price_val * quantity * (1 + fee_rate_val), 2)

        # 使用当前平台的 host
        base_url = self.platform_host
        
        # 构建请求头（与真实请求一致）
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Origin": base_url,
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{base_url}/details/2873AAA7",  # 商品详情页
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }
        
        # 构建请求体（按真实请求顺序）
        form_data = {
            "goodid": params["goodid"],
            "cateid": params["cateid"],
            "quantity": str(quantity),
            "contact": contact,
            "email": "",
            "couponcode": "",
            "pwdforsearch1": "",
            "pwdforsearch2": "",
            "is_contact_limit": params["is_contact_limit"],
            "limit_quantity": params["limit_quantity"],
            "userid": params["userid"],
            "token": params["token"],
            "cardNoLength": params["cardNoLength"],
            "cardPwdLength": params["cardPwdLength"],
            "is_discount": params["is_discount"],
            "coupon_ctype": params["coupon_ctype"],
            "coupon_value": params["coupon_value"],
            "sms_price": params["sms_price"],
            "paymoney": str(paymoney),
            "danjia": params["danjia"],
            "is_pwdforsearch": params["is_pwdforsearch"],
            "is_coupon": params["is_coupon"],
            "price": params["price"],
            "kucun": params["kucun"],
            "select_cards": params["select_cards"],
            "feePayer": params["feePayer"],
            "fee_rate": params["fee_rate"],
            "min_fee": params["min_fee"],
            "rate": params["rate"],
            "pid": "2",  # 支付宝（真实请求值）
        }

        # 输出步骤2的详细请求日志
        self._log(f"步骤2 URL: {base_url}/pay/order")
        # self._log(f"步骤2 请求体: {form_data}")
        # self._log(f"步骤2 请求头: {headers}")
        # self._log(f"步骤2 Cookie: {dict(self.session.cookies)}")

        resp = self.session.post(
            f"{base_url}/pay/order",
            data=form_data,
            headers=headers,
            timeout=15
        )
        
        # self._log(f"步骤2 响应状态码: {resp.status_code}")
        # self._log(f"步骤2 响应头: {dict(resp.headers)}")
        # self._log(f"步骤2 响应体: {resp.text}")

        if resp.status_code != 200:
            raise Exception(f"步骤2请求失败: HTTP {resp.status_code}")

        # 解析 trade_no
        soup = BeautifulSoup(resp.text, "html.parser")
        trade_no_input = soup.find("input", {"name": "trade_no"})
        if not trade_no_input or not trade_no_input.get("value"):
            # 尝试从页面文本中提取
            match = re.search(r'trade_no["\s:=]+([\w]+)', resp.text)
            if match:
                return match.group(1)
            raise Exception(
                f"步骤2: 未找到 trade_no，可能库存不足或需要验证码。\n"
                f"响应摘要: {resp.text[:200]}"
            )

        return trade_no_input.get("value")

    def _step25_check_buyer(self, orderid):
        """步骤2.5: 调用check_buyer验证指纹（四云发卡需要）"""
        import uuid
        
        # 生成或获取指纹（模拟浏览器的localStorage）
        # 尝试从session中获取已保存的指纹
        fingerprint = getattr(self, '_fingerprint', None)
        if not fingerprint:
            # 生成新的指纹（模拟浏览器的guid()函数）
            fingerprint = str(uuid.uuid4())
            self._fingerprint = fingerprint
            self._log(f"生成新的设备指纹: {fingerprint}")
        
        # 获取wxauth（可能为空）
        wxauth = getattr(self, '_wxauth', "")
        
        base_url = self.platform_host
        url = f"{base_url}/index/pay/check_buyer"
        
        data = {
            "trade_no": orderid,
            "fingerprint": fingerprint,
            "wxauth": wxauth
        }
        
        self._log(f"步骤2.5 URL: {url}")
        # self._log(f"步骤2.5 请求体: trade_no={orderid}&fingerprint={fingerprint}&wxauth={wxauth}")
        
        resp = self.session.post(
            url,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "sec-ch-ua-platform": '"Windows"',
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
                "sec-ch-ua-mobile": "?0",
                "Origin": base_url,
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": f"{base_url}/pay/order",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Priority": "u=0, i"
            },
            timeout=15
        )
        
        # self._log(f"步骤2.5 响应状态码: {resp.status_code}")
        # self._log(f"步骤2.5 响应体: {resp.text}")
        
        if resp.status_code != 200:
            raise Exception(f"步骤2.5请求失败: HTTP {resp.status_code}")
        
        try:
            result = resp.json()
            status = result.get("status", "")
            msg = result.get("msg", "")
            
            if status == "tip":
                raise Exception(f"步骤2.5: 指纹验证被拒绝 - {msg}")
            elif status == "collect":
                # 需要关注公众号，跳过继续尝试
                self._log(f"步骤2.5: 需要关注公众号，尝试继续...")
            else:
                # status 为空或其他值，表示验证通过
                self._log(f"步骤2.5: 指纹验证通过")
        except Exception as e:
            if "步骤2.5" in str(e):
                raise
            # JSON解析失败，忽略
            self._log(f"步骤2.5: 响应非JSON格式")

    def _step3_get_alipay_form(self, cookie, orderid):
        """步骤3: 获取支付宝支付表单（四云发卡返回302重定向）"""
        base_url = self.platform_host

        headers = {
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{base_url}/pay/order",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }

        # 拼接完整的URL（包含查询参数）
        full_url = f"{base_url}/index/pay/payment?trade_no={orderid}&agree=on"
        
        self._log(f"步骤3 URL: {full_url}")
        # self._log(f"步骤3 请求头: {headers}")
        # self._log(f"步骤3 Cookie: {dict(self.session.cookies)}")

        resp = self.session.get(
            full_url,
            headers=headers,
            timeout=15,
            allow_redirects=False  # 禁止自动重定向
        )

        # self._log(f"步骤3 响应状态码: {resp.status_code}")
        # self._log(f"步骤3 响应头: {dict(resp.headers)}")

        # 四云发卡：处理 302 重定向
        if resp.status_code in (302, 301):
            location = resp.headers.get("Location")
            if not location:
                raise Exception("步骤3: 响应头中无 Location 字段")
            self._log(f"步骤3 重定向地址: {location}")
            # 返回重定向地址，等待下一步处理
            return {"redirect_url": location}
        
        if resp.status_code != 200:
            raise Exception(f"步骤3请求失败: HTTP {resp.status_code}")

        # 兼容猴发卡：解析 form#alipaysubmit
        soup = BeautifulSoup(resp.text, "html.parser")
        form = soup.find("form", {"id": "alipaysubmit"})
        if not form:
            raise Exception(f"步骤3: 未找到支付宝表单。\n响应体: {resp.text}")

        alipay_params = {}
        for inp in form.find_all("input", {"type": "hidden"}):
            name = inp.get("name")
            value = inp.get("value")
            if name and value is not None:
                alipay_params[name] = value

        if not alipay_params:
            raise Exception("步骤3: 支付宝表单参数为空")

        return alipay_params

    def _step35_get_alipay_form_from_redirect(self, redirect_url, cookie):
        """步骤3.5: 请求重定向地址，获取支付宝表单（四云发卡专用）"""
        self._log(f"步骤3.5 URL: {redirect_url}")
        
        headers = {
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{self.platform_host}/index/pay/payment",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }
        
        # self._log(f"步骤3.5 请求头: {headers}")
        # self._log(f"步骤3.5 Cookie: {dict(self.session.cookies)}")
        
        resp = self.session.get(
            redirect_url,
            headers=headers,
            timeout=15
        )
        
        # self._log(f"步骤3.5 响应状态码: {resp.status_code}")
        # self._log(f"步骤3.5 响应头: {dict(resp.headers)}")
        # self._log(f"步骤3.5 响应体: {resp.text}")
        
        if resp.status_code != 200:
            raise Exception(f"步骤3.5请求失败: HTTP {resp.status_code}")
        
        # 解析 HTML，查找支付宝表单 form#alipaysubmit
        soup = BeautifulSoup(resp.text, "html.parser")
        form = soup.find("form", {"id": "alipaysubmit"})
        if not form:
            raise Exception(f"步骤3.5: 未找到支付宝表单。\n响应体: {resp.text}")
        
        # 提取表单参数
        alipay_params = {}
        for inp in form.find_all("input", {"type": "hidden"}):
            name = inp.get("name")
            value = inp.get("value")
            if name and value is not None:
                alipay_params[name] = value
        
        if not alipay_params:
            raise Exception("步骤3.5: 支付宝表单参数为空")
        
        return alipay_params

    def _step4_request_alipay_gateway(self, alipay_params):
        """步骤4: 请求支付宝网关，获取第一次重定向地址"""
        gateway_url = "https://openapi.alipay.com/gateway.do"

        # 按真实请求顺序重组参数
        ordered_params = OrderedDict()
        param_order = [
            "app_id", "method", "format", "return_url", "charset",
            "sign_type", "timestamp", "version", "notify_url",
            "biz_content", "sign",
        ]
        for key in param_order:
            if key in alipay_params:
                ordered_params[key] = alipay_params[key]
        # 追加剩余未知参数
        for key, val in alipay_params.items():
            if key not in ordered_params:
                ordered_params[key] = val

        # 固定参数覆盖（使用真实请求的值）
        ordered_params["method"] = "alipay.trade.wap.pay"
        ordered_params["return_url"] = f"{self.platform_host}/pay/alipay_wap/callback.html"
        # 注意：notify_url 使用真实值
        ordered_params["notify_url"] = "http://not.pay.4yun.4yuns.com/pay/Alipay_Wap/notify"
        ordered_params["charset"] = "utf-8"

        # 修改 biz_content 中的 product_code
        if "biz_content" in ordered_params:
            try:
                biz = json.loads(ordered_params["biz_content"])
            except (json.JSONDecodeError, TypeError):
                biz = {}
            biz["product_code"] = "QUICK_WAP_WAY"
            # 整个 biz_content 用 ensure_ascii=True 实现 USC2 编码
            ordered_params["biz_content"] = json.dumps(biz, separators=(",", ":"), ensure_ascii=True)

        # URL 编码参数（charset作为URL参数）
        encoded_data = urlencode(ordered_params)
        
        # 完整URL包含charset参数
        full_url = f"{gateway_url}?charset=utf-8"

        # 完整浏览器请求头
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Origin": self.platform_host,
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{self.platform_host}/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
        }

        self._log(f"步骤4 URL: {full_url}")
        # self._log(f"步骤4 请求体: {encoded_data}")

        resp = self.session.post(
            full_url,
            data=encoded_data,
            headers=headers,
            timeout=15,
            allow_redirects=False  # 禁止自动重定向，手动处理
        )

        if resp.status_code not in (302, 301):
            raise Exception(
                f"步骤4: 预期 302 重定向，实际 HTTP {resp.status_code}\n"
                f"响应摘要: {resp.text[:200]}"
            )

        location1 = resp.headers.get("Location")
        if not location1:
            raise Exception(f"步骤4: 响应头中无 Location 字段")

        # 提取支付宝 Cookie
        alipay_cookies = {}
        set_cookie_headers = resp.headers.get("set-cookie", "")
        if set_cookie_headers:
            # 解析多个 cookie（按分号分隔）
            for cookie_str in set_cookie_headers.split(";"):
                cookie_str = cookie_str.strip()
                if "=" in cookie_str and not cookie_str.startswith(("Domain", "Path", "HttpOnly", "Secure", "Expires", "Max-Age", "SameSite")):
                    key, val = cookie_str.split("=", 1)
                    alipay_cookies[key.strip()] = val.split(";")[0].strip()
            # 二次解析：按逗号分隔的多 Set-Cookie
            if not alipay_cookies:
                for cookie_str in set_cookie_headers.split(","):
                    cookie_str = cookie_str.strip()
                    if "=" in cookie_str:
                        key, val = cookie_str.split("=", 1)
                        alipay_cookies[key.strip()] = val.split(";")[0].strip()

        return location1, alipay_cookies

    def _step5_follow_redirect(self, location1, alipay_cookies):
        """步骤5: 跟随重定向，获取最终支付链接"""
        # 构建 Cookie 字符串：合并 alipay_cookies + session 中已有的 Cookie
        session_cookies = "; ".join([f"{k}={v}" for k, v in self.session.cookies.items()])
        alipay_cookie_str = "; ".join([f"{k}={v}" for k, v in alipay_cookies.items()])

        # 合并两者，去重（alipay_cookies 优先）
        all_cookies = {}
        # 先加入 session 中的 cookie
        for k, v in self.session.cookies.items():
            all_cookies[k] = v
        # 再加入 alipay_cookies（覆盖同名）
        for k, v in alipay_cookies.items():
            all_cookies[k] = v

        cookie_str = "; ".join([f"{k}={v}" for k, v in all_cookies.items()])

        # 完整浏览器请求头
        headers = {
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{self.platform_host}/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
            "Cookie": cookie_str if cookie_str else "",
        }

        # self._log(f"步骤5 Cookie: {list(all_cookies.keys())}")

        resp = self.session.get(
            location1,
            headers=headers,
            timeout=15,
            allow_redirects=False
        )

        if resp.status_code not in (302, 301):
            # 有时可能直接返回200（已经是最终页面）
            if resp.status_code == 200:
                self._log("提示: 步骤5直接返回200，使用当前URL")
                return resp.url

            raise Exception(
                f"步骤5: 预期 302 重定向，实际 HTTP {resp.status_code}\n"
                f"响应摘要: {resp.text[:200]}"
            )

        final_pay_url = resp.headers.get("Location")
        if not final_pay_url:
            raise Exception("步骤5: 响应头中无 Location 字段")

        return final_pay_url

    def _step55_get_cashier_page(self, cashier_url, alipay_cookies):
        """步骤5.5: 访问支付宝收银台页面，提取二维码图片URL"""
        # 合并 Cookie
        all_cookies = {}
        for k, v in self.session.cookies.items():
            all_cookies[k] = v
        for k, v in alipay_cookies.items():
            all_cookies[k] = v

        cookie_str = "; ".join([f"{k}={v}" for k, v in all_cookies.items()])

        headers = {
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{self.platform_host}/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Priority": "u=0, i",
            "Cookie": cookie_str if cookie_str else "",
        }

        resp = self.session.get(cashier_url, headers=headers, timeout=15)

        if resp.status_code != 200:
            raise Exception(f"步骤5.5请求失败: HTTP {resp.status_code}")

        # 解析 HTML 提取二维码链接
        soup = BeautifulSoup(resp.text, "html.parser")

        # 方法1（优先）: 查找隐藏 input[name="qrCode"]
        qr_input = soup.find("input", {"name": "qrCode"})
        if qr_input and qr_input.get("value"):
            qr_url = qr_input.get("value")
            self._log(f"从隐藏input[name=qrCode]找到二维码链接: {qr_url}")
            return qr_url

        # 方法2: 通过 id="J_qrCode" 查找
        qr_input = soup.find("input", {"id": "J_qrCode"})
        if qr_input and qr_input.get("value"):
            qr_url = qr_input.get("value")
            self._log(f"从id=J_qrCode找到二维码链接: {qr_url}")
            return qr_url

        # 方法3: 从 hidden-input-area 容器中查找
        hidden_area = soup.find(id="hidden-input-area")
        if hidden_area:
            for inp in hidden_area.find_all("input"):
                if inp.get("value") and "qr.alipay.com" in inp.get("value", ""):
                    qr_url = inp.get("value")
                    self._log(f"从hidden-input-area找到二维码链接: {qr_url}")
                    return qr_url

        # 方法4: 从 JS 变量中提取
        for script in soup.find_all("script"):
            if script.string:
                patterns = [
                    r'qrCodeUrl\s*[:=]\s*["\']([^"\']+)["\']',
                    r'var\s+qrCode\s*=\s*["\']([^"\']+)["\']',
                    r'qrcode\s*[:=]\s*["\']([^"\']+)["\']',
                ]
                for pattern in patterns:
                    match = re.search(pattern, script.string)
                    if match:
                        src = match.group(1)
                        self._log(f"从JS变量找到二维码链接: {src}")
                        return src

        raise Exception("步骤5.5: 未能在页面中找到二维码链接（qrCode）")

    def _step6_generate_qrcode(self, url):
        """步骤6: 生成二维码并显示（旧方法，保留备用）"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((250, 250), Image.LANCZOS)

        self.current_qr_image = img.copy()

        photo = ImageTk.PhotoImage(img)
        self.root.after(0, lambda: self.qr_label.config(image=photo, text=""))
        self.qr_label.image = photo

    # ==================== 浏览器自动化 ====================

    def _display_qr_image(self, pil_image):
        """显示 PIL Image 到 GUI"""
        img = pil_image.resize((250, 250), Image.LANCZOS)
        self.current_qr_image = img.copy()

        photo = ImageTk.PhotoImage(img)
        self.root.after(0, lambda: self.qr_label.config(image=photo, text=""))
        self.qr_label.image = photo

    def _launch_headless_browser(self):
        """启动无头浏览器并应用 stealth 补丁，返回 (playwright, browser, context, page)"""
        pw = sync_playwright().start()
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=self.session.headers.get("User-Agent", ""),
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        return pw, browser, context, page

    def _extract_qr_from_payment_page(self, location1, alipay_cookies):
        """使用无头浏览器导航到支付页面并提取二维码图片"""
        pw, browser, context, page = None, None, None, None
        try:
            pw, browser, context, page = self._launch_headless_browser()

            # 设置 Alipay Cookie
            for key, value in alipay_cookies.items():
                context.add_cookies([{
                    "name": key,
                    "value": value,
                    "domain": ".alipay.com",
                    "path": "/",
                }])

            # 导航到支付页面
            self._log("正在打开支付页面...")
            page.goto(location1, wait_until="networkidle", timeout=60000)

            # 等待二维码元素出现（多种选择器）
            self._log("等待二维码渲染...")
            selectors = [
                'img[src*="qr"]',
                'img[src*="QR"]',
                'img[src*="barcode"]',
                'img[src^="data:image"]',
                'canvas',
                '.qr-code img',
                '.pay-qrcode img',
                '.alipay-qrcode img',
                '#qrCode img',
                'img.qrcode',
            ]

            qr_element = None
            for selector in selectors:
                try:
                    qr_element = page.wait_for_selector(selector, timeout=5000)
                    if qr_element:
                        self._log(f"找到二维码元素: {selector}")
                        break
                except Exception:
                    continue

            if not qr_element:
                # 最后尝试：取页面中第一个 img 或 canvas
                try:
                    qr_element = page.wait_for_selector("img, canvas", timeout=5000)
                    if qr_element:
                        self._log("使用默认元素作为二维码")
                except Exception:
                    pass

            if not qr_element:
                raise Exception("未能找到二维码元素，页面可能加载失败或结构变化")

            # 提取二维码图片
            self._log("提取二维码图片...")
            tag_name = qr_element.evaluate("el => el.tagName")

            if tag_name == "IMG":
                src = qr_element.get_attribute("src") or ""
                if src.startswith("data:image"):
                    # data URL
                    data = src.split(",", 1)[1]
                    img_bytes = base64.b64decode(data)
                else:
                    # HTTP URL，通过浏览器获取
                    response = page.request.get(src)
                    img_bytes = response.body()
            else:
                # canvas 或其他元素，截图
                img_bytes = qr_element.screenshot()

            # 转为 PIL Image
            img = Image.open(BytesIO(img_bytes)).convert("RGB")
            return img

        except Exception as e:
            self._log(f"浏览器操作异常: {e}")
            raise
        finally:
            if page:
                try:
                    page.close()
                except Exception:
                    pass
            if context:
                try:
                    context.close()
                except Exception:
                    pass
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass
            if pw:
                try:
                    pw.stop()
                except Exception:
                    pass

    def _step5_browser_extract(self, location1, alipay_cookies):
        """步骤5: 使用浏览器提取二维码"""
        self._log("步骤5: 使用无头浏览器访问支付页面...")
        qr_image = self._extract_qr_from_payment_page(location1, alipay_cookies)
        self._log("成功: 从支付页面提取二维码图片")
        return qr_image

    # ==================== Cookie 持久化 ====================

    def _load_merchant_cookies(self):
        """加载已保存的商户 Cookie"""
        if not os.path.exists(self.cookie_file):
            return

        try:
            with open(self.cookie_file, 'rb') as f:
                saved_data = pickle.load(f)

            username = saved_data.get('username', '')
            cookies_list = saved_data.get('cookies', [])
            login_time = saved_data.get('login_time', '')

            # 重建 Session
            self.merchant_session = requests.Session()
            self.merchant_session.verify = False
            self.merchant_session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
            })

            # 恢复 Cookie
            for cookie in cookies_list:
                self.merchant_session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', '.4yuns.com'))
                # 提取 s1c9ae71b Cookie 供支付二维码流程复用
                if 's1c9ae71b' in cookie['name'].lower():
                    self.saved_s1c9ae71b = cookie['value']

            # 验证 Cookie 是否有效
            if self._verify_merchant_cookie():
                self.merchant_logged_in = True
                self.merchant_username = username
                self._log(f"成功: 从文件加载已保存的登录状态 (用户: {username}, 登录时间: {login_time})")
                if self.saved_s1c9ae71b:
                    self._log(f"成功: 从文件加载 s1c9ae71b Cookie: {self.saved_s1c9ae71b[:10]}...")
            else:
                self._log("提示: 已保存的 Cookie 已失效，需要重新登录")
                self.merchant_session = None
        except Exception as e:
            self._log(f"提示: 加载保存的 Cookie 失败 - {e}")
            self.merchant_session = None

    def _save_merchant_cookies(self, username):
        """保存商户 Cookie 到文件"""
        try:
            cookies_list = []
            for cookie in self.merchant_session.cookies:
                cookies_list.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                })

            saved_data = {
                'username': username,
                'cookies': cookies_list,
                'login_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            with open(self.cookie_file, 'wb') as f:
                pickle.dump(saved_data, f)

            self._log(f"成功: 商户 Cookie 已保存至 {self.cookie_file}")
        except Exception as e:
            self._log(f"错误: 保存商户 Cookie 失败 - {e}")

    def _load_url_config(self):
        """加载已保存的商品链接"""
        if not os.path.exists(self.url_config_file):
            return

        try:
            with open(self.url_config_file, 'rb') as f:
                saved_url = pickle.load(f)

            if saved_url:
                self._log(f"成功: 从文件加载已保存的商品链接: {saved_url[:50]}...")
                # 在 UI 创建后设置商品链接
                self.root.after(200, lambda: self.url_entry.insert(0, saved_url))
        except Exception as e:
            self._log(f"提示: 加载保存的商品链接失败 - {e}")

    def _save_url_config(self, url):
        """保存商品链接到文件"""
        try:
            with open(self.url_config_file, 'wb') as f:
                pickle.dump(url, f)

            self._log(f"成功: 商品链接已保存至 {self.url_config_file}")
        except Exception as e:
            self._log(f"错误: 保存商品链接失败 - {e}")

    def _load_credentials(self):
        """加载已保存的登录凭证"""
        if not os.path.exists(self.credentials_file):
            return None, None

        try:
            with open(self.credentials_file, 'rb') as f:
                credentials = pickle.load(f)

            username = credentials.get('username', '')
            password = credentials.get('password', '')
            
            if username and password:
                self._log(f"成功: 从文件加载已保存的登录凭证 (用户: {username})")
                return username, password
        except Exception as e:
            self._log(f"提示: 加载保存的登录凭证失败 - {e}")
        
        return None, None

    def _save_credentials(self, username, password):
        """保存登录凭证到文件"""
        try:
            credentials = {
                'username': username,
                'password': password,
                'save_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            with open(self.credentials_file, 'wb') as f:
                pickle.dump(credentials, f)

            self._log(f"成功: 登录凭证已保存至 {self.credentials_file}")
        except Exception as e:
            self._log(f"错误: 保存登录凭证失败 - {e}")

    def _verify_merchant_cookie(self):
        """验证商户 Cookie 是否有效"""
        if not self.merchant_session:
            return False

        try:
            # 根据当前平台验证商户后台
            verify_url = f"{self.platform_host}/merchant/index.html"
            resp = self.merchant_session.get(
                verify_url,
                timeout=10,
                allow_redirects=False
            )

            # 如果返回 200 或未重定向到登录页，说明 Cookie 有效
            if resp.status_code == 200:
                return True

            # 检查是否被重定向到登录页
            location = resp.headers.get('Location', '')
            if 'login' in location.lower():
                return False

            return True
        except Exception:
            return False


def main():
    root = tk.Tk()
    app = AutoOrderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
