# 使用 Python 3.12 作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装 Node.js 18.x
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    # 清理 apt 缓存以减小镜像大小
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 验证安装
RUN python --version && node --version && npm --version

COPY requirements.txt .
# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .


RUN npm install

# 设置默认命令
CMD ["npm", "start"]
