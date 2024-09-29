import sys
import os
import time
import ast
import json
import subprocess
import requests

argv = sys.argv

def download_file(url):
    # HTTPリクエストを送信
    try:
        response = requests.get(url, stream=True,)
    except Exception as e:
        print(f"リクエスト中にエラーが発生しました: {e}")
        return None

    # レスポンスのステータスコードを確認
    if response.status_code != 200:
        print(f"エラー: {response.status_code} - {response.reason}")
        return None

    # ダウンロードしたデータをメモリに保存
    file_data = b''  # バイナリデータを格納するための変数
    total_size = int(response.headers.get('Content-Length', 0))  # 合計サイズを取得
    downloaded_size = 0  # ダウンロード済みサイズを初期化
    start_time = time.time()  # 開始時間を記録

    for chunk in response.iter_content(chunk_size=1024):
        file_data += chunk  # チャンクを追加
        downloaded_size += len(chunk)  # ダウンロード済みサイズを更新

        # プログレスバーを表示
        progress_bar(downloaded_size, total_size, start_time)

    print(f'\nダウンロード完了: {len(file_data)} バイト')
    return file_data

def progress_bar(downloaded_size, total_size, start_time):
    percent = downloaded_size / total_size * 100
    bar_length = 10  # プログレスバーの長さを10に設定
    block = int(bar_length * percent / 100)

    elapsed_time = time.time() - start_time
    eta = (total_size / downloaded_size - 1) * elapsed_time if downloaded_size > 0 else 0

    # プログレスバーの表示
    bar = '#' * block + '-' * (bar_length - block)
    sys.stdout.write(f'\r[{bar}] {downloaded_size}/{total_size} バイト ETA: {int(eta)}秒')
    sys.stdout.flush()

# コマンドライン引数からURLと名前を取得
URL = argv[argv.index("-url") + 1]
Name = argv[argv.index("-name") + 1]

Response = download_file(URL)

if Response is None:
    sys.exit(1)

File = Response

os.makedirs("./Importer_Build", exist_ok=True)
os.chdir("./Importer_Build")

# モジュールを保存
with open(f"{Name}_Module.py", "wb") as f:
    f.write(File)

print("ダウンロードが完了しました。")
sys.stdout.write("pipパッケージ構造を構築しています･･･")

os.makedirs("./temp", exist_ok=True)
os.chdir("./temp")
os.makedirs(f"./{Name}", exist_ok=True)
os.chdir(f"./{Name}")

with open("./__init__.py", "wb") as f:
    f.write(File)

os.chdir("../")

# ソースコードをパースしてASTを生成
tree = ast.parse(File)

# インポートされたモジュールを格納するリスト
imported_modules = []

# ノードを走査
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for alias in node.names:
            imported_modules.append(alias.name)
    elif isinstance(node, ast.ImportFrom):
        imported_modules.append(node.module)

# 重複を取り除く
imported_modules = list(set(imported_modules))

SetupData = f"""from setuptools import setup, find_packages

setup(
    name="{Name}",  # パッケージ名
    version="0.1",     # バージョン番号
    author="Auto Build", # 架空の名前
    packages=find_packages(), # パッケージを自動的に検出
    install_requires={json.dumps(imported_modules)}
)
"""

with open("./setup.py", "w", encoding="utf-8") as f:
    f.write(SetupData)

sys.stdout.write("Done\n")

sys.stdout.write("pipでビルドしています･･･")

try:
    subprocess.run([sys.executable, "setup.py", "sdist", "bdist_wheel"], check=True)
except subprocess.CalledProcessError:
    sys.stdout.write("エラー: ビルドに失敗しました。\n")
    sys.exit(1)

try:
    subprocess.run([sys.executable, "-m", "pip", "install", f"./dist/{Name}-0.1.tar.gz"], check=True)
except subprocess.CalledProcessError:
    sys.stdout.write("エラー: インストールに失敗しました。\n")
    sys.exit(1)

sys.stdout.write("Done\n")
