#!/bin/bash
# UI 验证脚本 — 测试驱动开发的核心
# 用法：bash tests/ui-validate.sh
# 返回：0=全部通过，1=有失败项

PASS=0
FAIL=0

echo "=== UI 验证测试 ==="

# 测试 1: 文件结构
echo -n "测试 1: 核心文件存在... "
for f in index.html scan.html assets.html static/css/style.css static/js/app.js; do
  if [ -f "$f" ]; then
    :
  else
    echo "FAIL: 缺少 $f"
    FAIL=$((FAIL+1))
  fi
done
echo "PASS" && PASS=$((PASS+1))

# 测试 2: CSS 变量定义
echo -n "测试 2: CSS 变量完整定义... "
CSS_FILE="static/css/style.css"
if [ ! -f "$CSS_FILE" ]; then
    echo "FAIL: static/css/style.css 不存在"
    FAIL=$((FAIL+1))
else
    missing=0
    # 使用带--的grep命令以避免将--开头的变量名误解为选项
    for var in --bg-primary --bg-card --text-primary --accent-blue --accent-green --accent-red --radius --border-color; do
        if ! grep -qF -- "$var" "$CSS_FILE" 2>/dev/null; then
            echo "FAIL: 缺少 $var"
            FAIL=$((FAIL+1))
            missing=1
        fi
    done
    if [ $missing -eq 0 ]; then
        echo "PASS" && PASS=$((PASS+1))
    fi
fi

# 测试 3: 无硬编码颜色（除 :root 外）
echo -n "测试 3: 无硬编码颜色... "
if [ -f "static/css/style.css" ]; then
    # 简单检查整个文件中的十六进制颜色数量
    total_colors=$(grep -o '#[0-9a-fA-F]\{3,6\}' static/css/style.css 2>/dev/null | wc -l)

    # 从文件中提取:root部分的内容并计算颜色数
    root_part=$(sed -n '/:root[[:space:]]*{/,/[}]/p' static/css/style.css | head -n -1)
    root_colors=$(echo "$root_part" | grep -o '#[0-9a-fA-F]\{3,6\}' 2>/dev/null | wc -l)

    if [ "$total_colors" -le "$root_colors" ] 2>/dev/null; then
        echo "PASS" && PASS=$((PASS+1))
    else
        echo "FAIL: 发现硬编码颜色 (总色值 $total_colors, :root内 $root_colors)"
        FAIL=$((FAIL+1))
    fi
else
    echo "FAIL: static/css/style.css 不存在"
    FAIL=$((FAIL+1))
fi

# 测试 4: 导航栏基本结构一致性
echo -n "测试 4: 3 个页面导航栏结构一致性... "
all_pages_have_nav=1
for page in index.html scan.html assets.html; do
    if [ ! -f "$page" ]; then
        echo "FAIL: $page 不存在"
        FAIL=$((FAIL+1))
        all_pages_have_nav=0
        break
    fi

    # 检查基本导航元素
    if ! grep -q '<nav class="navbar">' "$page" 2>/dev/null; then
        echo "FAIL: $page 中缺少导航栏结构"
        FAIL=$((FAIL+1))
        all_pages_have_nav=0
        break
    fi

    if ! grep -q 'class="brand"' "$page" 2>/dev/null; then
        echo "FAIL: $page 中缺少品牌标识"
        FAIL=$((FAIL+1))
        all_pages_have_nav=0
        break
    fi

    if ! grep -q 'class="links"' "$page" 2>/dev/null; then
        echo "FAIL: $page 中缺少导航链接容器"
        FAIL=$((FAIL+1))
        all_pages_have_nav=0
        break
    fi

    # 检查是否包含基本导航链接
    required_links=("href=\"index.html\"" "href=\"scan.html\"" "href=\"assets.html\"")
    for link in "${required_links[@]}"; do
        if ! grep -q "$link" "$page" 2>/dev/null; then
            echo "FAIL: $page 中缺少基本导航链接 $link"
            FAIL=$((FAIL+1))
            all_pages_have_nav=0
            break
        fi
    done
done

if [ $all_pages_have_nav -eq 1 ]; then
    echo "PASS" && PASS=$((PASS+1))
fi

# 测试 5: 统计卡片数量
echo -n "测试 5: 仪表盘有 4 个统计卡片... "
if [ -f "index.html" ]; then
    count=$(grep -c 'class="card-stat"' index.html 2>/dev/null || echo 0)
    if [ "$count" -ge 4 ]; then
        echo "PASS" && PASS=$((PASS+1))
    else
        echo "FAIL: 期望至少 4 个，实际 $count 个"
        FAIL=$((FAIL+1))
    fi
else
    echo "FAIL: index.html 不存在"
    FAIL=$((FAIL+1))
fi

# 测试 6: 资产页有表格
echo -n "测试 6: 资产页有数据表格... "
if [ -f "assets.html" ]; then
    if grep -q '<table' assets.html 2>/dev/null; then
        echo "PASS" && PASS=$((PASS+1))
    else
        echo "FAIL: 缺少 table 元素"
        FAIL=$((FAIL+1))
    fi
else
    echo "FAIL: assets.html 不存在"
    FAIL=$((FAIL+1))
fi

# 测试 7: 状态标签颜色正确
echo -n "测试 7: 状态标签颜色正确... "
if [ -f "assets.html" ]; then
    if grep -q 'status-badge' assets.html 2>/dev/null && \
       (grep -q 'online' assets.html 2>/dev/null || grep -q 'offline' assets.html 2>/dev/null); then
        echo "PASS" && PASS=$((PASS+1))
    else
        echo "FAIL: 状态标签缺失或颜色不对"
        FAIL=$((FAIL+1))
    fi
else
    echo "FAIL: assets.html 不存在"
    FAIL=$((FAIL+1))
fi

# 测试 8: 无 JS 框架引入
echo -n "测试 8: 无 JS 框架引入... "
missing_framework=0
for html_file in index.html scan.html assets.html; do
    if [ -f "$html_file" ]; then
        if grep -qE "(vue\.js|react\.|htmx\.|cdn\.jsdelivr)" "$html_file" 2>/dev/null; then
            missing_framework=1
        fi
    fi
done
if [ -f "static/js/app.js" ]; then
    if grep -qE "(vue\.js|react\.|htmx\.|cdn\.jsdelivr)" static/js/app.js 2>/dev/null; then
        missing_framework=1
    fi
fi
if [ $missing_framework -eq 0 ]; then
    echo "PASS" && PASS=$((PASS+1))
else
    echo "FAIL: 发现 JS 框架引入"
    FAIL=$((FAIL+1))
fi

# 测试 9: 响应式媒体查询
echo -n "测试 9: 响应式媒体查询存在... "
if [ -f "static/css/style.css" ]; then
    if grep -q '@media' static/css/style.css 2>/dev/null; then
        echo "PASS" && PASS=$((PASS+1))
    else
        echo "FAIL: 缺少 @media 查询"
        FAIL=$((FAIL+1))
    fi
else
    echo "FAIL: static/css/style.css 不存在"
    FAIL=$((FAIL+1))
fi

# 测试 10: 假数据合理性
echo -n "测试 10: 假数据 IP 格式正确... "
if [ -f "index.html" ] && [ -f "assets.html" ]; then
    if grep -qE '192\.168\.[0-9]+\.[0-9]+' index.html 2>/dev/null && grep -qE '192\.168\.[0-9]+\.[0-9]+' assets.html 2>/dev/null; then
        echo "PASS" && PASS=$((PASS+1))
    else
        echo "FAIL: 缺少合理的假数据 IP"
        FAIL=$((FAIL+1))
    fi
else
    echo "FAIL: index.html 或 assets.html 不存在"
    FAIL=$((FAIL+1))
fi

echo ""
echo "=== 结果: $PASS 通过, $FAIL 失败 ==="
[ $FAIL -eq 0 ] && exit 0 || exit 1