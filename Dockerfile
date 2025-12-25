# 使用 Python 3.12 作为基础镜像
FROM python:3.12-slim

# 设置环境变量，避免交互式提示
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 更新系统并安装必要工具 (git, nodejs, npm, build-essential for compiling deps)
RUN apt-get update && apt-get install -y \
    git \
    nodejs \
    npm \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /workspace

# 1. 克隆所有仓库
# MaimConfigs (注意: 假设 MaimConfig 也在 Mai-with-u 组织下，如果不是，需要调整)
RUN git clone https://github.com/Mai-with-u/MaimConfig.git
RUN git clone https://github.com/Mai-with-u/MaimWebBackend.git
RUN git clone https://github.com/Mai-with-u/MaimWeb.git
RUN git clone https://github.com/Mai-with-u/maim_db.git
# COPY . /workspace/maim_db
RUN git clone https://github.com/Mai-with-u/maim_message.git

# MaiMBot (特殊分支 saas)
RUN git clone -b saas https://github.com/tcmofashi/MaiMBot.git

# 2. 安装 Python 依赖
# 为了方便管理，我们创建一个聚合的 requirements.txt 或者逐个安装

# maim_db
WORKDIR /workspace/maim_db
RUN pip install .
RUN pip install aiosqlite

# MaimConfig
WORKDIR /workspace/MaimConfig
RUN pip install -r requirements.txt

# MaimWebBackend (Uses pyproject.toml)
WORKDIR /workspace/MaimWebBackend
RUN pip install .

# MaiMBot
WORKDIR /workspace/MaiMBot
RUN pip install -r requirements.txt

# maim_message (Uses pyproject.toml/setup.py)
WORKDIR /workspace/maim_message
RUN pip install .

# 3. 构建前端 MaimWeb
WORKDIR /workspace/MaimWeb
RUN npm install
RUN npm run build

# 4. 回到根目录
WORKDIR /workspace

# 暴露端口 (根据各服务默认端口)
# MaimConfig: 8000
# MaimWebBackend: 8880
# MaimWeb: 5173 (Dev) or Nginx port
# MaiMBot: 8090 (WebSocket)

EXPOSE 8000 8880 5173 8090

# 启动脚本 (需要另外创建一个 start_all.sh entrypoint)
COPY start_all_docker.sh /workspace/start_all_docker.sh
RUN chmod +x /workspace/start_all_docker.sh

ENTRYPOINT ["/workspace/start_all_docker.sh"]
