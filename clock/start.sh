#!/bin/bash

# 启动 Flask 后端
echo "正在启动 Flask 后端..."
cd backend || exit  # 进入后端目录，如果失败则退出
nohup python app.py > flask.log 2>&1 &  # 后端以后台进程方式运行，将日志输出到 flask.log
FLASK_PID=$!  # 获取 Flask 进程的 PID

# 检查 Flask 是否成功启动
if ps -p $FLASK_PID > /dev/null
then
   echo "Flask 后端已启动 (PID: $FLASK_PID)."
else
   echo "Flask 后端启动失败。"
   exit 1
fi

sleep 3

# 启动 React 前端
echo "正在启动 React 前端..."
cd ../frontend || exit  # 进入前端目录，如果失败则退出
npm start  # 启动前端，保留前端在前台

# 结束脚本时关闭 Flask 后端进程
trap 'echo "关闭 Flask 后端 (PID: $FLASK_PID)"; kill $FLASK_PID' EXIT