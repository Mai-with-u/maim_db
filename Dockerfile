# Dockerfile for All-in-One MaiMBot Environment
#
# 使用方法 (在包含所有项目的父目录下运行):
# docker build -t maim-all-in-one -f maim_db/Dockerfile .
#
# 启动容器 (挂载数据目录):
# docker run -d -p 8000:8000 -p 18042:18042 -p 8880:8880 -p 5173:5173 -v $(pwd)/data:/app/data maim-all-in-one

# -----------------------------------------------------------------------------
# Stage 1: 基础镜像构建 (包含 Python 和 Node.js)
# -----------------------------------------------------------------------------
FROM python:3.12-slim as base

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖 (包含 Node.js, ffmpeg, git, supervisord, openssh-server)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ffmpeg \
    supervisor \
    openssh-server \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# SSH 配置
RUN mkdir /var/run/sshd \
    && echo 'root:root' | chpasswd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    # 修复 PAM导致的连接断开问题
    && sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

# 设置工作目录
WORKDIR /app

# -----------------------------------------------------------------------------
# Stage 2: 依赖安装 (利用 Docker 缓存层级)
# -----------------------------------------------------------------------------
# 1. 优先复制并安装基础库 (maim_db, maim_message)
# 假设构建上下文是项目根目录，包含 maim_db, maim_message 等文件夹

# maim_db 依赖
COPY maim_db/pyproject.toml maim_db/requirements.t[xt] /app/maim_db/
# maim_message 依赖
COPY maim_message/pyproject.toml maim_message/requirements.t[xt] /app/maim_message/

# 安装基础库 (暂不复制代码，只安装依赖)
# 注意：如果 pyproject.toml 包含动态版本号读取，可能需要源码。
# 这里先安装依赖文件中的包
RUN if [ -f /app/maim_db/requirements.txt ]; then pip install -r /app/maim_db/requirements.txt; fi \
    && if [ -f /app/maim_message/requirements.txt ]; then pip install -r /app/maim_message/requirements.txt; fi

# 2. 复制应用层依赖
COPY MaimConfig/requirements.txt /app/MaimConfig/
COPY MaiMBot/requirements.txt /app/MaiMBot/
COPY MaimWebBackend/requirements.txt /app/MaimWebBackend/
COPY MaimWeb/package.json MaimWeb/package-lock.jso[n] /app/MaimWeb/

# 3. 安装应用层依赖 (Python)
RUN pip install -r /app/MaimConfig/requirements.txt \
    && pip install -r /app/MaiMBot/requirements.txt \
    && pip install -r /app/MaimWebBackend/requirements.txt

# 4. 安装前端依赖 (Node)
WORKDIR /app/MaimWeb
RUN npm install
WORKDIR /app

# -----------------------------------------------------------------------------
# Stage 3: 代码注入与最终配置
# -----------------------------------------------------------------------------
# 注意：作为开发环境，我们不再复制源码到镜像中，而是通过 docker-compose 挂载
# 这样不仅构建更快，而且修改代码无需重建镜像
# COPY ... (已移除)

# 创建必要的目录
RUN mkdir -p /app/data /app/logs

# 生成 Supervisor 配置文件
# 注意：因为源码是运行时挂载的，这里只生成配置，不检查文件是否存在
RUN echo "[supervisord]\n\
    nodaemon=true\n\
    logfile=/app/logs/supervisord.log\n\
    \n\
    [program:sshd]\n\
    command=/usr/sbin/sshd -D\n\
    stdout_logfile=/dev/stdout\n\
    stdout_logfile_maxbytes=0\n\
    stderr_logfile=/dev/stderr\n\
    stderr_logfile_maxbytes=0\n\
    \n\
    [program:maimconfig]\n\
    command=python src/main.py\n\
    directory=/app/MaimConfig\n\
    stdout_logfile=/dev/stdout\n\
    stdout_logfile_maxbytes=0\n\
    stderr_logfile=/dev/stderr\n\
    stderr_logfile_maxbytes=0\n\
    environment=DATABASE_URL='sqlite+aiosqlite:////app/data/MaiBot.db'\n\
    \n\
    [program:maimbot]\n\
    command=python bot.py\n\
    directory=/app/MaiMBot\n\
    stdout_logfile=/dev/stdout\n\
    stdout_logfile_maxbytes=0\n\
    stderr_logfile=/dev/stderr\n\
    stderr_logfile_maxbytes=0\n\
    environment=MAIMCONFIG_URL='http://localhost:8000',DATABASE_URL='sqlite+aiosqlite:////app/data/MaiBot.db'\n\
    \n\
    [program:maimwebbackend]\n\
    command=python start.py\n\
    directory=/app/MaimWebBackend\n\
    stdout_logfile=/dev/stdout\n\
    stdout_logfile_maxbytes=0\n\
    stderr_logfile=/dev/stderr\n\
    stderr_logfile_maxbytes=0\n\
    environment=MAIMCONFIG_API_URL='http://localhost:8000/api/v1',DATABASE_URL='sqlite+aiosqlite:////app/data/MaiBot.db'\n\
    \n\
    [program:maimweb]\n\
    command=npm run dev -- --host 0.0.0.0\n\
    directory=/app/MaimWeb\n\
    stdout_logfile=/dev/stdout\n\
    stdout_logfile_maxbytes=0\n\
    stderr_logfile=/dev/stderr\n\
    stderr_logfile_maxbytes=0\n\
    " > /etc/supervisor/conf.d/maim_all.conf

# 环境变量设置
# 通过 PYTHONPATH 让 Python 能直接引用挂载进来的 maim_db 和 maim_message
ENV PYTHONPATH=/app/maim_db/src:/app/maim_message/src:$PYTHONPATH
ENV MAIM_ENV=production

# 暴露端口
# 22: SSH
# 8000: MaimConfig
# 18042: MaiMBot WebSocket
# 8880: MaimWebBackend
# 5173: MaimWeb Frontend (Vite Dev)
EXPOSE 22 8000 18042 8880 5173

# 启动命令
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/maim_all.conf"]
