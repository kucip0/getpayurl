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
