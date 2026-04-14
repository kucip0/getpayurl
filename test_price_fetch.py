"""
测试猴发卡价格获取功能 - 使用数据库中的Cookie
"""
import json
import os
import sqlite3
import requests
from bs4 import BeautifulSoup

# 清除SSL环境变量
for env_var in ['REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE', 'SSLKEYLOGFILE']:
    if env_var in os.environ:
        del os.environ[env_var]
        print(f"已删除环境变量: {env_var}")

# 数据库路径
DB_PATH = r"D:\Project\Qoder\GetPayurl\web\backend\getpayurl.db"

# 测试商品URL
TEST_PRODUCT_URL = "https://www.houfaka.com/details/40418"

def load_cookies_from_db():
    """从数据库加载Cookie"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查询houfaka平台的配置
    cursor.execute("""
        SELECT id, user_id, platform_code, cookies 
        FROM platform_configs 
        WHERE platform_code = 'houfaka'
    """)
    
    configs = cursor.fetchall()
    print(f"找到 {len(configs)} 个houfaka配置:")
    for config in configs:
        print(f"  ID={config[0]}, user_id={config[1]}, platform_code={config[2]}")
        if config[3]:
            cookies = json.loads(config[3])
            print(f"  Cookie数量: {len(cookies)}")
            for cookie in cookies[:3]:  # 只显示前3个
                print(f"    {cookie['name']}={cookie['value'][:30]}...")
    
    # 返回第一个配置的cookies
    if configs:
        return json.loads(configs[0][3]) if configs[0][3] else []
    
    return []

def test_price_fetch(cookies):
    """测试价格获取"""
    print(f"\n=== 测试价格获取 ===")
    print(f"商品URL: {TEST_PRODUCT_URL}")
    print(f"Cookie数量: {len(cookies)}")
    
    # 创建session
    session = requests.Session()
    session.verify = False
    
    # 设置headers（与Web版本一致）
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    })
    
    # 设置cookies
    for cookie in cookies:
        session.cookies.set(
            cookie["name"],
            cookie["value"],
            domain=cookie.get("domain"),
        )
    
    print(f"已设置 {len(session.cookies)} 个cookie")
    print(f"Cookie列表: {list(session.cookies.keys())}")
    
    # 请求商品页面
    try:
        resp = session.get(TEST_PRODUCT_URL, timeout=15)
        print(f"HTTP状态码: {resp.status_code}")
        print(f"HTML长度: {len(resp.text)}")
        print(f"HTML内容预览: {resp.text[:200]}")
        
        # 测试方法1：直接解析（原始项目方式）
        print(f"\n--- 方法1：直接解析（原始项目方式）---")
        soup1 = BeautifulSoup(resp.text, "html.parser")
        price_span1 = soup1.find("span", class_="card__detail_price")
        if price_span1:
            price_text1 = price_span1.get_text().strip()
            price1 = price_text1.replace("￥", "").replace("¥", "")
            print(f"价格: ¥{price1}")
        else:
            print("未找到价格span")
        
        goods_box1 = soup1.find("div", class_="goods_box")
        if goods_box1:
            h3_tag1 = goods_box1.find("h3")
            if h3_tag1:
                print(f"商品名称: {h3_tag1.get_text().strip()}")
            else:
                print("未找到h3标签")
        else:
            print("未找到goods_box")
        
        # 测试方法2：HTML反转义后解析（当前Web版本方式）
        print(f"\n--- 方法2：HTML反转义后解析（当前Web版本）---")
        html = resp.text.replace('\\/', '/').replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
        soup2 = BeautifulSoup(html, "html.parser")
        price_span2 = soup2.find("span", class_="card__detail_price")
        if price_span2:
            price_text2 = price_span2.get_text().strip()
            price2 = price_text2.replace("￥", "").replace("¥", "")
            print(f"价格: ¥{price2}")
        else:
            print("未找到价格span")
        
        # 检查input元素
        print(f"\n--- 检查input元素 ---")
        inputs = soup1.find_all("input", attrs={"name": True})
        print(f"方法1找到 {len(inputs)} 个input")
        for inp in inputs[:5]:
            print(f"  name={inp['name']}, value={inp.get('value', '')[:30]}")
        
        inputs2 = soup2.find_all("input", attrs={"name": True})
        print(f"方法2找到 {len(inputs2)} 个input")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cookies = load_cookies_from_db()
    if cookies:
        test_price_fetch(cookies)
    else:
        print("没有找到Cookie数据")
