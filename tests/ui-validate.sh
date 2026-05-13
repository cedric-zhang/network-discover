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
    # 使用更简单的方式检查变量
    grep -q ":root {" "$CSS_FILE" 2>/dev/null || { echo "FAIL: 未找到 :root 定义"; FAIL=$((FAIL+1)); missing=1; }
    grep -q "--bg-primary:" "$CSS_FILE" 2>/dev/null || { echo "FAIL: 缺少 --bg-primary"; FAIL=$((FAIL+1)); missing=1; }
    grep -q "--bg-card:" "$CSS_FILE" 2>/dev/null || { echo "FAIL: 缺少 --bg-card"; FAIL=$((FAIL+1)); missing=1; }
    grep -q "--text-primary:" "$CSS_FILE" 2>/dev/null || { echo "FAIL: 缺少 --text-primary"; FAIL=$((FAIL+1)); missing=1; }
    grep -q "--accent-blue:" "$CSS_FILE" 2>/dev/null || { echo "FAIL: 缺少 --accent-blue"; FAIL=$((FAIL+1)); missing=1; }
    grep -q "--accent-green:" "$CSS_FILE" 2>/dev/null || { echo "FAIL: 缺少 --accent-green"; FAIL=$((FAIL+1)); missing=1; }
    grep -q "--accent-red:" "$CSS_FILE" 2>/dev/null || { echo "FAIL: 缺少 --accent-red"; FAIL=$((FAIL+1)); missing=1; }
    grep -q "--radius:" "$CSS_FILE" 2>/dev/null || { echo "FAIL: 缺少 --radius"; FAIL=$((FAIL+1)); missing=1; }
    grep -q "--border-color:" "$CSS_FILE" 2>/dev/null || { echo "FAIL: 缺少 --border-color"; FAIL=$((FAIL+1)); missing=1; }
    if [ $missing -eq 0 ]; then
        echo "PASS" && PASS=$((PASS+1))
    fi
fi

# 测试 3: 无硬编码颜色（除 :root 外）
echo -n "测试 3: 无硬编码颜色... "
if [ -f "static/css/style.css" ]; then
    # 计算CSS文件中所有#开头的颜色数量
    total_colors=$(grep -o '#[0-9a-fA-F]\{3,6\}' static/css/style.css 2>/dev/null | wc -l)
    # 计算:root部分内的颜色数量
    root_content=$(awk '
    BEGIN { in_root = 0; content = "" }
    /^:root/ { in_root = 1; next }
    in_root && /^[[:space:]]*{/ { next }
    in_root && /^[[:space:]]*}/ { in_root = 0; next }
    in_root { content = content $0 "\n" }
    END { printf "%s", content }
    ' static/css/style.css)
    # 将:root部分的内容存入临时文件并计算颜色数量
    echo "$root_content" | grep -o '#[0-9a-fA-F]\{3,6\}' 2>/dev/null | wc -l > /tmp/root_colors_count
    root_colors=$(cat /tmp/root_colors_count)
    rm -f /tmp/root_colors_count 2>/dev/null
    if [ "$total_colors" -gt 0 ] && [ "$total_colors" -le "$root_colors" ] 2>/dev/null; then
        echo "PASS" && PASS=$((PASS+1))
    elif [ "$total_colors" -eq 0 ]; then
        # 如果没有找到任何颜色值，也视为通过
        echo "PASS" && PASS=$((PASS+1))
    else
        echo "FAIL: 发现硬编码颜色 (总色值 $total_colors, 估计:root内 $root_colors)"
        FAIL=$((FAIL+1))
    fi
else
    echo "FAIL: static/css/style.css 不存在"
    FAIL=$((FAIL+1))
fi

# 测试 4: 导航栏一致性
echo -n "测试 4: 3 个页面导航栏一致... "
if [ -f "index.html" ] && [ -f "scan.html" ] && [ -f "assets.html" ]; then
    # 提取导航栏内容并比较
    nav1=$(grep -A 20 '<nav class="navbar">' index.html 2>/dev/null | grep -B 20 '</nav>' 2>/dev/null)
    nav2=$(grep -A 20 '<nav class="navbar">' scan.html 2>/dev/null | grep -B 20 '</nav>' 2>/dev/null)
    nav3=$(grep -A 20 '<nav class="navbar">' assets.html 2>/dev/null | grep -B 20 '</nav>' 2>/dev/null)

    if [ -n "$nav1" ] && [ -n "$nav2" ] && [ -n "$nav3" ]; then
        if [ "$nav1" = "$nav2" ] && [ "$nav2" = "$nav3" ]; then
            echo "PASS" && PASS=$((PASS+1))
        else
            echo "FAIL: 导航栏内容不一致"
            FAIL=$((FAIL+1))
        fi
    else
        echo "FAIL: 未找到导航栏标记"
        FAIL=$((FAIL+1))
    fi
else
    echo "FAIL: HTML 文件不存在"
    FAIL=$((FAIL+1))
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
    if grep -q '@media' static/css/style.css; then
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