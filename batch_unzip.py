import os
import shutil
import zipfile
import rarfile
import py7zr
from pathlib import Path

# 配置解压目录
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')

def extract_archive(file_path, extract_to):
    """解压单个压缩文件"""
    try:
        if file_path.lower().endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif file_path.lower().endswith('.rar'):
            with rarfile.RarFile(file_path) as rar_ref:
                rar_ref.extractall(extract_to)
        elif file_path.lower().endswith('.7z'):
            with py7zr.SevenZipFile(file_path, mode='r') as sevenz_ref:
                sevenz_ref.extractall(extract_to)
        else:
            print(f"不支持的文件格式: {file_path}")
            return False
        return True
    except Exception as e:
        print(f"解压失败 {file_path}: {str(e)}")
        return False

def batch_unzip():
    """批量解压所有学生提交的压缩文件"""
    if not os.path.exists(UPLOAD_FOLDER):
        print(f"上传目录不存在: {UPLOAD_FOLDER}")
        return

    for root, dirs, files in os.walk(UPLOAD_FOLDER):
        for file in files:
            file_path = os.path.join(root, file)
            if any(file.lower().endswith(ext) for ext in ['.zip', '.rar', '.7z']):
                print(f"正在解压: {file_path}")
                if extract_archive(file_path, root):
                    # 解压成功后删除原压缩文件
                    os.remove(file_path)
                    print(f"成功解压并删除: {file_path}")
                else:
                    print(f"解压失败: {file_path}")

if __name__ == '__main__':
    print("开始批量解压...")
    batch_unzip()
    print("批量解压完成")
