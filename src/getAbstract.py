import platform
from DrissionPage import WebPage, ChromiumOptions
import requests
import re
import json
import time


# URL = "https://doi.org/10.1109/hpcc67675.2025.00214"
# URL = "https://dl.acm.org/doi/10.1145/3716368.3735198"


# 从ACM数据库获取摘要
def getAbstractFromACM(URL):

    # 配置浏览器路径
    if platform.system().lower() == "windows":
        co = ChromiumOptions().set_paths(browser_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    else:
        co = ChromiumOptions().set_paths(browser_path=r"/opt/google/chrome/google-chrome")

    # 浏览器参数
    co.headless(True) # 设置无头模式
    co.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0") # 设置user-agent
    co.incognito(True) # 设置无痕模式
    # co.set_argument("--guest") # 设置访客模式
    # co.set_argument("--no-sandbox") # 设置沙箱模式
    co.set_argument("--disable-gpu") # 设置禁用GPU

    browser = WebPage("d", chromium_options=co)
    browser.get(URL, retry=3, interval=2, timeout=15)
    time.sleep(2) 

    html = browser.html
    browser.quit()
    abstract = ""
    # 正则匹配 <div role="paragraph">...</div>
    match = re.search(r'<div\s+role="paragraph"\s*>(.*?)</div>', html, re.S)

    if match:
        abstract = re.sub(r'<[^>]+>', '', match.group(1)).strip()
    else:
        abstract = "None"
    
    return abstract

    # if match:
    #     text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
    #     print(text)
    # else:
    #     print("未找到摘要")

    

# 从IEEE数据库获取摘要
def getAbstractFromIEEE(URL):

    # 设置常见的浏览器请求头，模拟 Chrome 访问
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/141.0.0.0 Safari/537.36"
        )
    }

    resp = requests.get(URL, headers=headers, timeout=15)
    html = resp.text
    resp.close()
    time.sleep(2)

    m_meta = re.search(r'xplGlobal\.document\.metadata\s*=\s*(\{.*?\});', html, re.S)
    abstract = ""
    if m_meta:
        meta_raw = m_meta.group(1)
        meta = json.loads(meta_raw)
        abstract = meta.get("abstract")

    return abstract

    # if abstract:
    #     print(abstract.strip())
    # else:
    #     print("未找到 abstract")


# getAbstractFromACM(URL)
# getAbstractFromIEEE(URL)