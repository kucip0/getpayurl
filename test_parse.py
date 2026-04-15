"""测试订单表格解析"""
import sys
sys.path.append('web/backend')

from app.utils.html_parser import unescape_html, parse_order_table

# 读取真实响应数据
with open('web/response.txt', 'r', encoding='utf-8') as f:
    response_text = f.read()

# 提取HTML部分（跳过HTTP头）
html_start = response_text.find('<!DOCTYPE html>')
html_content = response_text[html_start:] if html_start != -1 else response_text

# 处理转义
html_processed = unescape_html(html_content)

# 解析订单
orders = parse_order_table(html_processed)

print(f"解析到 {len(orders)} 个订单\n")

if orders:
    for i, order in enumerate(orders, 1):
        print(f"订单 {i}:")
        for key, value in order.items():
            print(f"  {key}: {value}")
        print()
else:
    print("未解析到订单！")
    print("\n调试信息：")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_processed, "html.parser")
    
    # 检查表格
    table = soup.find("table", class_="table mb-0")
    print(f"  找到表格: {table is not None}")
    
    if table:
        tbody = table.find("tbody")
        print(f"  找到tbody: {tbody is not None}")
        
        if tbody:
            rows = tbody.find_all("tr")
            print(f"  找到tr行数: {len(rows)}")
            
            if rows:
                first_row = rows[0]
                cols = first_row.find_all(["th", "td"])
                print(f"  第一行列数: {len(cols)}")
                
                # 打印每列内容
                for j, col in enumerate(cols):
                    text = col.get_text().strip()
                    print(f"    列{j}: {text[:50]}")
