# 使用官方Python基础镜像
FROM python:3.9-slim

# 设置中文编码环境
WORKDIR /app

# 设置locale环境变量
ENV LANG=zh_CN.UTF-8
ENV LC_ALL=zh_CN.UTF-8

# 配置容器使用宿主机代理
ENV HTTP_PROXY=http://host.docker.internal:7890
ENV HTTPS_PROXY=http://host.docker.internal:7890


# 复制requirements文件
COPY requirements.txt .

# 配置pip使用国内镜像源并安装依赖
RUN pip install --no-cache-dir -r requirements.txt \
    --proxy=http://host.docker.internal:7890

# 复制项目文件
COPY . .

# 使用Python库进行文件解压
RUN pip install --no-cache-dir py7zr rarfile

# 创建上传目录
RUN mkdir -p /app/uploads
RUN mkdir -p /app/backend/config

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# 启动命令
# 优化Gunicorn配置：4 worker进程 + 2线程/进程 + gevent异步
CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
    "--workers", "4", \
    "--threads", "2", \
    "--worker-class", "gevent", \
    "--timeout", "300", \
    "--keep-alive", "60", \
    "app:app"]
