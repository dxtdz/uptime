import subprocess
import threading
import time
import requests
import os
import signal
import sys
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Biến toàn cục để lưu trạng thái tunnel
tunnel_process = None
tunnel_url = None
is_running = False

# HTML Template cho trang chủ
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TryCloudFlare Tunnel Tool</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
            color: #333;
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 30px;
        }
        .url-box {
            background: #f5f5f5;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
            word-break: break-all;
        }
        .url-link {
            color: #667eea;
            font-size: 18px;
            font-weight: bold;
            text-decoration: none;
        }
        .url-link:hover {
            text-decoration: underline;
        }
        .button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            margin: 10px;
            transition: transform 0.3s ease;
        }
        .button:hover {
            transform: translateY(-2px);
        }
        .button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .status {
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-weight: bold;
        }
        .status-active {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status-inactive {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .info-text {
            font-size: 14px;
            color: #666;
            margin-top: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 TryCloudFlare Tunnel Tool</h1>
        
        <div class="status" id="status" class="status-inactive">
            Trạng thái: Đang kiểm tra...
        </div>

        <div class="url-box" id="urlBox" style="display: none;">
            <h3>🌐 URL Tunnel của bạn:</h3>
            <a href="#" id="tunnelUrl" class="url-link" target="_blank"></a>
            <br>
            <button class="button" onclick="copyUrl()">📋 Copy URL</button>
        </div>

        <div style="text-align: center;">
            <button class="button" id="startBtn" onclick="startTunnel()">▶️ Bắt đầu Tunnel</button>
            <button class="button" id="stopBtn" onclick="stopTunnel()" disabled>⏹️ Dừng Tunnel</button>
            <button class="button" onclick="checkStatus()">🔄 Kiểm tra trạng thái</button>
        </div>

        <div class="info-text">
            <p>Tool này sử dụng TryCloudFlare để tạo tunnel tạm thời.</p>
            <p>Lưu ý: Tunnel sẽ tự động dừng sau 2 giờ hoặc khi bạn đóng ứng dụng.</p>
        </div>
    </div>

    <script>
        async function checkStatus() {
            try {
                const response = await fetch('/status');
                const data = await response.json();
                
                const statusDiv = document.getElementById('status');
                const urlBox = document.getElementById('urlBox');
                const tunnelUrl = document.getElementById('tunnelUrl');
                const startBtn = document.getElementById('startBtn');
                const stopBtn = document.getElementById('stopBtn');

                if (data.is_running && data.url) {
                    statusDiv.className = 'status status-active';
                    statusDiv.textContent = 'Trạng thái: Đang hoạt động';
                    urlBox.style.display = 'block';
                    tunnelUrl.href = data.url;
                    tunnelUrl.textContent = data.url;
                    startBtn.disabled = true;
                    stopBtn.disabled = false;
                } else {
                    statusDiv.className = 'status status-inactive';
                    statusDiv.textContent = 'Trạng thái: Đang dừng';
                    urlBox.style.display = 'none';
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                }
            } catch (error) {
                console.error('Lỗi:', error);
            }
        }

        async function startTunnel() {
            try {
                const response = await fetch('/start', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    alert('Đã bắt đầu tunnel thành công!');
                    checkStatus();
                } else {
                    alert('Lỗi: ' + data.error);
                }
            } catch (error) {
                alert('Lỗi kết nối đến server');
            }
        }

        async function stopTunnel() {
            try {
                const response = await fetch('/stop', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    alert('Đã dừng tunnel thành công!');
                    checkStatus();
                } else {
                    alert('Lỗi: ' + data.error);
                }
            } catch (error) {
                alert('Lỗi kết nối đến server');
            }
        }

        function copyUrl() {
            const url = document.getElementById('tunnelUrl').textContent;
            navigator.clipboard.writeText(url).then(() => {
                alert('Đã copy URL vào clipboard!');
            });
        }

        // Kiểm tra trạng thái mỗi 5 giây
        setInterval(checkStatus, 5000);
        
        // Kiểm tra trạng thái ban đầu
        checkStatus();
    </script>
</body>
</html>
"""

def install_cloudflared():
    """Cài đặt cloudflared nếu chưa có"""
    try:
        # Kiểm tra xem cloudflared đã được cài đặt chưa
        subprocess.run(['cloudflared', '--version'], capture_output=True, check=True)
        logger.info("cloudflared đã được cài đặt")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.info("Đang cài đặt cloudflared...")
        try:
            # Tải và cài đặt cloudflared
            import platform
            system = platform.system().lower()
            
            if system == 'linux':
                subprocess.run([
                    'wget', '-q', 
                    'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64',
                    '-O', 'cloudflared'
                ], check=True)
                subprocess.run(['chmod', '+x', 'cloudflared'], check=True)
                subprocess.run(['sudo', 'mv', 'cloudflared', '/usr/local/bin/'], check=True)
            elif system == 'darwin':  # macOS
                subprocess.run(['brew', 'install', 'cloudflared'], check=True)
            elif system == 'windows':
                # Trên Windows, chúng ta sẽ dùng phiên bản portable
                subprocess.run([
                    'powershell', '-Command',
                    'Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "cloudflared.exe"'
                ], check=True)
            
            logger.info("Cài đặt cloudflared thành công")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi cài đặt cloudflared: {e}")
            return False

def start_cloudflared_tunnel():
    """Bắt đầu tunnel TryCloudFlare"""
    global tunnel_process, tunnel_url, is_running
    
    try:
        # Kiểm tra và cài đặt cloudflared
        if not install_cloudflared():
            logger.error("Không thể cài đặt cloudflared")
            return False
        
        # Khởi động một HTTP server đơn giản (nếu chưa có)
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        import threading
        
        def run_http_server():
            server = HTTPServer(('localhost', 8080), SimpleHTTPRequestHandler)
            server.serve_forever()
        
        http_thread = threading.Thread(target=run_http_server, daemon=True)
        http_thread.start()
        
        # Khởi động tunnel với cloudflared
        cmd = ['cloudflared', 'tunnel', '--url', 'http://localhost:8080']
        
        # Trên Windows, cần thêm shell=True
        if os.name == 'nt':
            tunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
        else:
            tunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        # Đọc output để lấy URL
        time.sleep(3)  # Đợi tunnel khởi động
        
        # Đọc output để tìm URL
        for line in tunnel_process.stderr:
            if 'https://' in line and '.trycloudflare.com' in line:
                # Trích xuất URL
                import re
                urls = re.findall(r'https://[^\s]+\.trycloudflare\.com', line)
                if urls:
                    tunnel_url = urls[0]
                    is_running = True
                    logger.info(f"Tunnel đã được tạo: {tunnel_url}")
                    break
        
        return True
        
    except Exception as e:
        logger.error(f"Lỗi khi tạo tunnel: {e}")
        return False

def stop_cloudflared_tunnel():
    """Dừng tunnel"""
    global tunnel_process, tunnel_url, is_running
    
    if tunnel_process:
        try:
            # Dừng process
            if os.name == 'nt':  # Windows
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(tunnel_process.pid)])
            else:  # Linux/Mac
                os.killpg(os.getpgid(tunnel_process.pid), signal.SIGTERM)
            
            tunnel_process.terminate()
            tunnel_process.wait(timeout=5)
        except:
            pass
        
        tunnel_process = None
        tunnel_url = None
        is_running = False
        logger.info("Đã dừng tunnel")

@app.route('/')
def index():
    """Trang chủ"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    """Kiểm tra trạng thái tunnel"""
    global is_running, tunnel_url
    return jsonify({
        'is_running': is_running,
        'url': tunnel_url if is_running else None
    })

@app.route('/start', methods=['POST'])
def start():
    """Bắt đầu tunnel"""
    global is_running
    
    if is_running:
        return jsonify({'success': False, 'error': 'Tunnel đang chạy'})
    
    success = start_cloudflared_tunnel()
    if success:
        return jsonify({'success': True, 'url': tunnel_url})
    else:
        return jsonify({'success': False, 'error': 'Không thể tạo tunnel'})

@app.route('/stop', methods=['POST'])
def stop():
    """Dừng tunnel"""
    global is_running
    
    if not is_running:
        return jsonify({'success': False, 'error': 'Không có tunnel nào đang chạy'})
    
    stop_cloudflared_tunnel()
    return jsonify({'success': True})

def cleanup(signum, frame):
    """Dọn dẹp khi thoát"""
    logger.info("Đang dọn dẹp...")
    stop_cloudflared_tunnel()
    sys.exit(0)

if __name__ == '__main__':
    # Đăng ký signal handler cho việc dọn dẹp
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Chạy Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
