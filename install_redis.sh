#!/bin/bash

# Redis 安装和配置脚本
# 用途：安装 Redis Server 并进行基本配置

echo "================================================"
echo " Redis 数据持久化 - 安装脚本"
echo "================================================"
echo ""

# 1. 更新包列表
echo "📦 步骤 1/5: 更新系统包列表..."
sudo apt update

echo ""
echo "✅ 包列表更新完成"
echo ""

# 2. 安装 Redis
echo "📦 步骤 2/5: 安装 Redis Server..."
sudo apt install redis-server -y

echo ""
echo "✅ Redis Server 安装完成"
echo ""

# 3. 启动 Redis 服务
echo "🚀 步骤 3/5: 启动 Redis 服务..."
sudo systemctl start redis-server

echo ""
echo "✅ Redis 服务已启动"
echo ""

# 4. 设置开机自启动
echo "⚙️  步骤 4/5: 设置开机自启动..."
sudo systemctl enable redis-server

echo ""
echo "✅ 已设置开机自启动"
echo ""

# 5. 验证安装
echo "🔍 步骤 5/5: 验证 Redis 安装..."
echo ""

echo "Redis 版本:"
redis-cli --version

echo ""
echo "Redis 服务状态:"
sudo systemctl status redis-server --no-pager | head -n 10

echo ""
echo "测试 Redis 连接:"
redis-cli ping

echo ""
echo "================================================"
echo " ✅ Redis 安装完成！"
echo "================================================"
echo ""
echo "📝 下一步："
echo "1. Redis 默认配置已启用（端口 6379）"
echo "2. Claude 将继续执行 Python 客户端安装和代码实现"
echo ""
echo "💡 可选配置（生产环境推荐）："
echo "编辑配置文件: sudo nano /etc/redis/redis.conf"
echo "- 启用 AOF 持久化: appendonly yes"
echo "- 设置内存限制: maxmemory 512mb"
echo "- 重启服务: sudo systemctl restart redis-server"
echo ""
