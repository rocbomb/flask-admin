# 使用 Python 3.12 的基础镜像
FROM python

# 设置工作目录
WORKDIR /app

# 复制代码到容器中
COPY ./examples/auth .

# 安装 Flask
RUN pip install -r req.txt --pre

# 暴露容器的端口
EXPOSE 5001

# 运行 Python 应用
CMD ["python", "app.py"]