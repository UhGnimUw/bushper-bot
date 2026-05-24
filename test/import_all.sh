#!/bin/bash
# 一键导入所有 tier 文档到 ChromaDB

set -e  # 出错立即退出

cd "$(dirname "$0")/.."  # 进入项目根目录

echo "=========================================="
echo "  开始导入所有 tier 文档"
echo "=========================================="
echo ""

# 导入 tier0
echo "📁 导入 tier0（绝密）文档..."
python test/put_vec_to_db.py -d data/t0 -l tier0 --clear
echo ""

# 导入 tier1
echo "📁 导入 tier1（机密）文档..."
python test/put_vec_to_db.py -d data/t1 -l tier1 --clear
echo ""

# 导入 tier2
echo "📁 导入 tier2（内部）文档..."
python test/put_vec_to_db.py -d data/t2 -l tier2 --clear
echo ""

# 导入 tier3
echo "📁 导入 tier3（公开）文档..."
python test/put_vec_to_db.py -d data/t3 -l tier3 --clear
echo ""

echo "=========================================="
echo "  ✅ 所有文档导入完成！"
echo "=========================================="
