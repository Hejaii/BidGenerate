#!/bin/bash

# 荔枝智慧果园投标项目占位符批量替换脚本
# 用法: ./fill_placeholders.sh [公司名称] [项目名称] [投标日期] [项目经理姓名]

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查参数
if [ $# -lt 4 ]; then
    echo -e "${RED}错误: 参数不足${NC}"
    echo "用法: $0 [公司名称] [项目名称] [投标日期] [项目经理姓名]"
    echo "示例: $0 '智慧科技有限公司' '荔枝智慧果园建设项目' '2024-12-20' '张三'"
    exit 1
fi

# 设置变量
COMPANY_NAME="$1"
PROJECT_NAME="$2"
BID_DATE="$3"
PROJECT_MANAGER="$4"

echo -e "${GREEN}开始批量替换占位符...${NC}"
echo "公司名称: $COMPANY_NAME"
echo "项目名称: $PROJECT_NAME"
echo "投标日期: $BID_DATE"
echo "项目经理: $PROJECT_MANAGER"
echo ""

# 获取脚本所在目录的上级目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 计数器
TOTAL_FILES=0
REPLACED_FILES=0

# 查找所有包含占位符的文件
find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.txt" -o -name "*.csv" \) | while read -r file; do
    if grep -q "{{" "$file"; then
        TOTAL_FILES=$((TOTAL_FILES + 1))
        echo -e "${YELLOW}处理文件: $file${NC}"
        
        # 执行替换
        sed -i.bak \
            -e "s/{{公司名称}}/$COMPANY_NAME/g" \
            -e "s/{{项目名称}}/$PROJECT_NAME/g" \
            -e "s/{{投标日期}}/$BID_DATE/g" \
            -e "s/{{项目经理姓名}}/$PROJECT_MANAGER/g" \
            -e "s/{{证书编号}}/待填写/g" \
            -e "s/{{联系人}}/待填写/g" \
            -e "s/{{联系电话}}/待填写/g" \
            -e "s/{{邮箱地址}}/待填写/g" \
            "$file"
        
        if [ $? -eq 0 ]; then
            REPLACED_FILES=$((REPLACED_FILES + 1))
            echo -e "${GREEN}✓ 替换完成${NC}"
        else
            echo -e "${RED}✗ 替换失败${NC}"
        fi
    fi
done

echo ""
echo -e "${GREEN}占位符替换完成！${NC}"
echo "总文件数: $TOTAL_FILES"
echo "成功替换: $REPLACED_FILES"

# 清理备份文件
echo "清理备份文件..."
find "$PROJECT_ROOT" -name "*.bak" -delete

echo -e "${GREEN}所有操作完成！${NC}"
echo ""
echo "注意事项:"
echo "1. 请检查替换后的内容是否正确"
echo "2. 对于证书编号等具体信息，请手动填写"
echo "3. 建议在提交前再次检查所有文件内容"
