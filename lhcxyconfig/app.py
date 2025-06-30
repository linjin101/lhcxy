from flask import Flask, request, render_template_string
from flask_httpauth import HTTPBasicAuth
import subprocess
import re
import os

app = Flask(__name__)

auth = HTTPBasicAuth()
users = {"admin": "lhcxy"}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

# 在所有路由上添加认证
@app.before_request
@auth.login_required
def require_login():
    pass



# 配置文件配置
CONFIGS = {
    'config1': {
        'path': 'C:/work/lhcxy/lhcxy/config/config.py',
        'pm2_cmd': ['pm2', 'restart', '1', '2'],
        'display': '配置1'
    },
    'config2': {
        'path': 'C:/work/lhcxy/lhcxy2/config/config.py',
        'pm2_cmd': ['pm2', 'restart', '3', '4'],
        'display': '配置2'
    },
    'config3': {
        'path': 'C:/work/lhcxy/lhcxy3/config/config.py',
        'pm2_cmd': ['pm2', 'restart', '5', '6'],
        'display': '配置3'
    }
}

# CONFIGS = {
#     'config1': {
#         'path': '/root/lhcxy/config/config.py',
#         'pm2_cmd': ['pm2', 'restart', '1', '2'],
#         'display': '配置1'
#     },
#     'config2': {
#         'path': '/root/lhcxy2/config/config.py',
#         'pm2_cmd': ['pm2', 'restart', '3', '4'],
#         'display': '配置2'
#     },
#     'config3': {
#         'path': '/root/lhcxy3/config/config.py',
#         'pm2_cmd': ['pm2', 'restart', '5', '6'],
#         'display': '配置3'
#     }
# }

# HTML模板 - 针对移动设备优化
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>多配置更新工具</title>
    <link rel="icon" type="image/x-icon" href="https://sanhu918.com/images/favicon.ico">
    <style>
        * {
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        body {
            background: #f5f7fa;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.08);
            width: 100%;
            max-width: 500px;
            padding: 30px;
        }
        h1 {
            color: #2d3748;
            text-align: center;
            font-size: 24px;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #718096;
            text-align: center;
            font-size: 15px;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #4a5568;
            font-weight: 500;
        }
        select, input {
            width: 100%;
            padding: 14px;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            font-size: 16px;
            transition: border-color 0.3s;
            background: white;
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
            background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%234a5568' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right 1rem center;
            background-size: 1.5em;
        }
        select:focus, input:focus {
            border-color: #4299e1;
            outline: none;
            box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.2);
        }
        .note {
            background: #ebf8ff;
            border-radius: 12px;
            padding: 15px;
            margin: 20px 0;
            font-size: 14px;
            color: #2b6cb0;
        }
        button {
            background: #4299e1;
            color: white;
            border: none;
            border-radius: 12px;
            padding: 16px;
            font-size: 17px;
            font-weight: 600;
            width: 100%;
            cursor: pointer;
            transition: background 0.3s;
            margin-top: 10px;
        }
        button:hover {
            background: #3182ce;
        }
        .result {
            margin-top: 25px;
            padding: 20px;
            border-radius: 12px;
            font-size: 16px;
        }
        .success {
            background: #f0fff4;
            color: #2f855a;
            border: 1px solid #c6f6d5;
        }
        .error {
            background: #fff5f5;
            color: #c53030;
            border: 1px solid #fed7d7;
        }
        .current {
            margin: 15px 0;
            padding: 12px;
            background: #edf2f7;
            border-radius: 8px;
            font-family: monospace;
            font-size: 14px;
        }
        .symbol-display {
            background: #e6fffa;
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
            font-weight: bold;
            color: #2c7a7b;
            text-align: center;
        }
         pre {
             white-space: pre-wrap;
             word-break: break-all;
             overflow-x: auto;
             font-family: monospace;
             background: rgba(0,0,0,0.05);
             padding: 10px;
             border-radius: 8px;
             max-width: 100%;
             font-size: 13px; /* 适当调小字体 */
           }
    </style>
</head>
<body>
    <div class="container">
        <h1>多配置更新工具</h1>
        <p class="subtitle">选择配置并更新交易对</p>

        <form method="POST" action="/update">
            <div class="form-group">
                <label for="config">选择配置:</label>
                <select id="config" name="config" required>
                    <option value="">-- 请选择配置 --</option>
                    {% for config_id, config_data in configs.items() %}
                    <option value="{{ config_id }}" {% if selected_config == config_id %}selected{% endif %}>
                        {{ config_data.display }}
                    </option>
                    {% endfor %}
                </select>
            </div>

            <div class="symbol-display" id="symbolDisplay">
                {% if current_symbol %}
                当前交易对: {{ current_symbol }}
                {% else %}
                请选择配置查看当前交易对
                {% endif %}
            </div>

            <div class="form-group">
                <label for="symbol">输入新交易对 (例如: LPT):</label>
                <input type="text" id="symbol" name="symbol" 
                       placeholder="输入交易对代码" 
                       required
                       oninput="this.value = this.value.toUpperCase()">
            </div>

            <div class="note">
                <strong>注意：</strong>
                <ul>
                    <li>输入的交易对代码将自动转换为大写字母</li>
                    <li>系统将自动添加 "-USDT-SWAP" 后缀</li>
                    <li>操作将修改配置文件并重启对应服务</li>
                    <li>不同配置对应不同的PM2进程组</li>
                </ul>
            </div>

            <button type="submit">更新并重启服务</button>
        </form>

        {% if message %}
        <div class="result {{ result_class }}">
            {{ message }}
            {% if command_output %}
            <div style="margin-top: 15px;">
                <strong>命令输出:</strong><br>
                <pre>{{ command_output }}</pre>
            </div>
            {% endif %}
        </div>
        {% endif %}
    </div>

    <script>
        // 当选择配置变化时，更新当前交易对显示
        document.getElementById('config').addEventListener('change', function() {
            const configId = this.value;
            
            // 获取选中项的显示文本
            const selectedText = this.options[this.selectedIndex].text.trim();

            if (configId) {
                fetch('/get-symbol?config=' + configId)
                    .then(response => response.json())
                    .then(data => {
                        const display = document.getElementById('symbolDisplay');
                        if (data.success) {
                            display.innerHTML = selectedText + `当前交易对: ${data.symbol}`;
                            display.style.display = 'block';
                        } else {
                            display.innerHTML = `错误: ${data.error}`;
                            display.style.color = '#c53030';
                        }
                    });
            } else {
                document.getElementById('symbolDisplay').innerHTML = '请选择配置查看当前交易对';
            }
        });

        // 页面加载时如果有选中的配置，自动获取一次
        window.addEventListener('DOMContentLoaded', function() {
            const configSelect = document.getElementById('config');
            if (configSelect.value) {
                configSelect.dispatchEvent(new Event('change'));
            }
        });
    </script>
</body>
</html>
"""


def get_symbol_from_config(config_path):
    """从配置文件中提取symbol值"""
    try:
        if not os.path.exists(config_path):
            return False, f"配置文件不存在: {config_path}", None

        # 修改这里：添加 encoding='utf-8' 参数
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 使用正则表达式匹配symbol值 - 修改为匹配任意长度的大写字母
        pattern = r"'symbol'\s*:\s*'([A-Z]+)-USDT-SWAP'"
        match = re.search(pattern, content)
        if match:
            return True, match.group(1), None
        else:
            # 尝试双引号匹配
            pattern = r'"symbol"\s*:\s*"([A-Z]+)-USDT-SWAP"'
            match = re.search(pattern, content)
            if match:
                return True, match.group(1), None
            return False, "未找到symbol配置", content

    except Exception as e:
        return False, f"读取错误: {str(e)}", None


def update_config(config_id, new_symbol):
    """更新配置文件并执行PM2重启"""
    config = CONFIGS.get(config_id)
    if not config:
        return False, f"无效的配置ID: {config_id}", ""

    config_path = config['path']
    pm2_cmd = config['pm2_cmd']

    try:
        # 转换为大写
        new_symbol = new_symbol.upper()

        # 读取配置文件
        if not os.path.exists(config_path):
            return False, f"配置文件不存在: {config_path}", ""

        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换配置值 - 修改为匹配任意长度的大写字母
        new_value = f"'{new_symbol}-USDT-SWAP'"
        pattern = r"('symbol'\s*:\s*)'[A-Z]+-USDT-SWAP'"
        new_content, count = re.subn(pattern, r"\1" + new_value, content)

        # 如果单引号匹配失败，尝试双引号
        if count == 0:
            pattern = r'("symbol"\s*:\s*)"[A-Z]+-USDT-SWAP"'
            new_content, count = re.subn(pattern, r'\1"' + new_symbol + '-USDT-SWAP"', content)

        if count == 0:
            return False, "未找到可替换的配置项", ""

        # 写回配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # 执行PM2重启命令
        result = subprocess.run(
            pm2_cmd,
            capture_output=True,
            text=True
        )

        # 检查命令结果
        if result.returncode != 0:
            return False, f"PM2重启失败 (代码:{result.returncode})", result.stderr

        return True, f"成功更新为 {new_symbol}-USDT-SWAP 并重启服务", result.stdout

    except Exception as e:
        return False, f"操作失败: {str(e)}", ""


@app.route('/', methods=['GET'])
def index():
    """主页面显示表单"""
    selected_config = request.args.get('config', '')
    current_symbol = ""

    if selected_config:
        success, symbol, _ = get_symbol_from_config(CONFIGS[selected_config]['path'])
        if success:
            current_symbol = symbol

    return render_template_string(
        HTML_TEMPLATE,
        configs=CONFIGS,
        selected_config=selected_config,
        current_symbol=current_symbol,
        message=None
    )


@app.route('/get-symbol', methods=['GET'])
def get_symbol():
    """API接口：获取指定配置的symbol值"""
    config_id = request.args.get('config')
    if not config_id or config_id not in CONFIGS:
        return {"success": False, "error": "无效的配置ID"}, 400

    config_path = CONFIGS[config_id]['path']
    success, symbol, _ = get_symbol_from_config(config_path)

    if success:
        return {"success": True, "symbol": symbol + "-USDT-SWAP"}
    else:
        return {"success": False, "error": symbol}


@app.route('/update', methods=['POST'])
def update():
    """处理表单提交"""
    config_id = request.form['config']
    symbol = request.form['symbol'].strip()

    if config_id not in CONFIGS:
        return render_template_string(
            HTML_TEMPLATE,
            configs=CONFIGS,
            selected_config=config_id,
            current_symbol="",
            message="错误: 无效的配置ID",
            result_class="error",
            command_output=""
        )

    success, message, output = update_config(config_id, symbol)

    # 获取更新后的symbol值
    _, new_symbol, _ = get_symbol_from_config(CONFIGS[config_id]['path'])

    return render_template_string(
        HTML_TEMPLATE,
        configs=CONFIGS,
        selected_config=config_id,
        current_symbol=new_symbol if new_symbol else "",
        message=message,
        result_class="success" if success else "error",
        command_output=output
    )


if __name__ == '__main__':
    # 注意：生产环境中应使用WSGI服务器如Gunicorn
    app.run(host='0.0.0.0', port=5000, debug=True)