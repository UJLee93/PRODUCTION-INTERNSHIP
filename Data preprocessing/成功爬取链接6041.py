from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import os

# -------------------- 配置 --------------------
BASE_URL = "https://www.pkulaw.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'Referer': BASE_URL
}

# -------------------- 提取链接函数 --------------------
def get_law_detail_info(html_content):
    """
    提取当前页面的法条名称 + 链接
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    laws = []
    for a in soup.select('h4 a[href*="/chl/"]'):
        title = a.get_text(strip=True)
        href = a['href'].split('?')[0]
        full_url = urljoin(BASE_URL, href)
        laws.append((title, full_url))
    return laws

# -------------------- 主流程 --------------------
if __name__ == "__main__":
    options = Options()
    # options.add_argument("--headless")  # 如果你不需要看到浏览器窗口，可取消注释
    driver = webdriver.Chrome(options=options)

    driver.get(BASE_URL)
    print("👉 请在浏览器中完成登录、筛选、滑块验证等操作。")

    wait = WebDriverWait(driver, 30)
    visited_urls = set()
    output_file = "法条详情链接_名字.txt"
    counter = 1  # 用于编号

    print("\n✅ 每次操作完页面后，按下回车，我将抓取当前页并等待下一轮。要退出程序请直接 Ctrl+C")

    while True:
        input("\n🔁 按回车抓取当前页面法条链接（你可以完成筛选/跳页/验证等后再操作）...")

        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.accompanying-wrap h4 a")))
        except:
            input("⚠️ 页面加载失败或等待超时，请处理验证后再按回车继续...")

        # 获取当前页源码
        page_source = driver.page_source
        law_infos = get_law_detail_info(page_source)

        new_count = 0
        with open(output_file, "a", encoding="utf-8") as f:
            for title, url in law_infos:
                if url not in visited_urls:
                    visited_urls.add(url)
                    f.write(f"{counter}、{title}：{url}\n")
                    counter += 1
                    new_count += 1

        print(f"✅ 本次抓取 {new_count} 条新法条链接，已追加到 {output_file}")
