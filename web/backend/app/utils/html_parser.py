import html as html_module
import re
from typing import Optional

from bs4 import BeautifulSoup


def unescape_html(html_content: str) -> str:
    """HTML反转义处理"""
    html_content = html_module.unescape(html_content)
    html_content = html_content.replace('\\/', '/')
    html_content = html_content.replace('\\"', '"')
    html_content = html_content.replace('\\n', '\n')
    html_content = html_content.replace('\\t', '\t')
    html_content = html_content.replace('\\\\', '\\')
    html_content = html_content.replace('&#x20;', ' ')
    return html_content


def extract_token_from_html(html: str, token_name: str = "__token__") -> Optional[str]:
    """从HTML中提取CSRF Token"""
    html = unescape_html(html)
    soup = BeautifulSoup(html, "html.parser")

    # 方法1: BeautifulSoup查找
    token_input = soup.find("input", {"name": token_name, "type": "hidden"})
    if token_input and token_input.get("value"):
        return token_input["value"]

    # 方法2: 正则表达式（5种模式）
    patterns = [
        rf'<input[^>]*name=["\']{token_name}["\'][^>]*value=["\']([^"\']+)["\']',
        rf'<input[^>]*value=["\']([^"\']+)["\'][^>]*name=["\']{token_name}["\']',
        rf'name=["\']{token_name}["\'][^>]*value=["\']([^"\']+)["\']',
        rf'<input[^>]*name=["\']{token_name}["\'][^>]*>',
        rf'<input[^>]*type=["\']hidden["\'][^>]*name=["\']{token_name}["\'][^>]*>',
    ]

    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            groups = match.groups()
            if groups:
                return groups[0]
            # 从完整标签中提取value
            tag_match = re.search(r'value=["\']([^"\']+)["\']', match.group(0))
            if tag_match:
                return tag_match.group(1)

    return None


def parse_form_data(form_element) -> dict:
    """解析表单数据为字典"""
    form_data = {}

    for input_elem in form_element.find_all(["input", "textarea", "select"]):
        name = input_elem.get("name")
        if not name:
            continue

        tag_type = input_elem.get("type", "text")

        if tag_type in ["hidden", "text", "number", "email"]:
            form_data[name] = input_elem.get("value", "")
        elif tag_type in ["radio", "checkbox"]:
            if input_elem.has_attr("checked"):
                form_data[name] = input_elem.get("value", "on")
        elif tag_type == "textarea":
            # 检查是否有Summernote编辑器
            summernote = input_elem.find_next_sibling("div", id=f"summernote-{name}")
            if summernote:
                form_data[name] = summernote.get_text()
            else:
                form_data[name] = input_elem.get_text()
        elif tag_type is None:  # select
            selected = input_elem.find("option", selected=True)
            if selected:
                form_data[name] = selected.get("value", "")
            elif input_elem.find("option"):
                form_data[name] = input_elem.find("option").get("value", "")

    return form_data


def parse_order_table(html: str) -> list[dict]:
    """
    解析猴发卡订单表格HTML，提取订单列表
    
    Args:
        html: 订单页面HTML内容（已处理转义）
        
    Returns:
        订单列表，每个订单为字典
    """
    soup = BeautifulSoup(html, "html.parser")
    orders = []
    
    # 定位订单表格
    table = soup.find("table", class_="table mb-0")
    if not table:
        return orders
    
    # 查找tbody
    tbody = table.find("tbody")
    if not tbody:
        return orders
    
    # 遍历每个订单行
    for tr in tbody.find_all("tr"):
        try:
            cols = tr.find_all(["th", "td"])
            if len(cols) < 12:  # 至少12列
                continue
            
            # 第1列：订单号（在th>a中）
            order_no = ""
            order_id = ""
            order_link = cols[0].find("a")
            if order_link:
                order_no = order_link.get_text().strip()
                href = order_link.get("href", "")
                # 从 href 提取 id 参数
                if "id=" in href:
                    order_id = href.split("id=")[-1].split("&")[0]
            
            # 第2列：订单类型
            order_type = ""
            badge = cols[1].find("span", class_="badge")
            if badge:
                order_type = badge.get_text().strip()
            else:
                order_type = cols[1].get_text().strip()
            
            # 第3列：商品名称（排除fetch链接）
            product_name = ""
            product_cell = cols[2]
            # 移除<a class="fetch">子标签
            fetch_link = product_cell.find("a", class_="fetch")
            if fetch_link:
                fetch_link.decompose()
            product_name = product_cell.get_text().strip()
            
            # 第4列：供货商（可能为空）
            supplier = cols[3].get_text().strip()
            
            # 第5列：支付方式
            payment_method = cols[4].get_text().strip()
            
            # 第6列：总价
            total_price = cols[5].get_text().strip()
            
            # 第7列：实付款
            actual_price = cols[6].get_text().strip()
            
            # 第8列：购买者信息
            buyer_info = cols[7].get_text().strip()
            
            # 第9列：状态
            status = ""
            status_badge = cols[8].find("span", class_="badge")
            if status_badge:
                status = status_badge.get_text().strip()
            else:
                status = cols[8].get_text().strip()
            
            # 第10列：取卡状态
            card_status = cols[9].get_text().strip()
            
            # 第11列：取卡密码（可能为空）
            card_password = cols[10].get_text().strip()
            
            # 第12列：交易时间
            trade_time = cols[11].get_text().strip()
            
            # 构建订单字典
            order = {
                "order_no": order_no,
                "order_type": order_type,
                "product_name": product_name,
                "supplier": supplier,
                "payment_method": payment_method,
                "total_price": total_price,
                "actual_price": actual_price,
                "buyer_info": buyer_info,
                "status": status,
                "card_status": card_status,
                "card_password": card_password,
                "trade_time": trade_time,
                "order_id": order_id,
            }
            
            orders.append(order)
            
        except Exception as e:
            # 跳过解析失败的行
            continue
    
    return orders
