import os
import json
import re
import requests
import feedparser
from datetime import datetime, date, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from getAbstract import getAbstractFromACM, getAbstractFromIEEE

# =============================
# 配置项（可按需修改）
# =============================

arXivCount = os.environ.get('ARXIV_COUNT', '5')
crossrefCount = os.environ.get('CROSSREF_COUNT', '5')

# 保存窗口大小
chunk_size = 10

# 通用网络超时（秒）
REQ_TIMEOUT = 20

# =============================
# 稳健会话（重试/退避/UA）
# =============================

def _session_with_retry():
    s = requests.Session()
    retries = Retry(
        total=3,                # 总重试次数
        connect=3,              # 连接重试
        read=3,                 # 读重试
        backoff_factor=0.5,     # 退避：0.5, 1, 2 ...
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["HEAD", "GET", "OPTIONS"])
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.headers.update({
        # 伪装常见浏览器 UA，减少被屏蔽概率
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    return s

SESSION = _session_with_retry()

# =============================
# 工具函数
# =============================

# 根据 URL 判定来源（ACM / IEEE / Unknown）
def guess_source(url):

    lower = (url or "").lower()
    if lower.startswith("https://doi.org/10.1145") or "dl.acm.org/doi/10.1145" in lower:
        return "ACM"
    if lower.startswith("https://doi.org/10.1109") or "ieeexplore.ieee.org" in lower:
        return "IEEE"
    return "Unknown"


def checkpoint_write(path, data):
    """覆盖写入到 JSON 文件，确保是一个完整的 JSON 数组。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 从任意字符串中提取 DOI（简单鲁棒版）
def _extract_doi(url: str):

    if not url:
        return None
    m = re.search(r"(10\.\d{4,9}/[^\s<>\"']+)", url)
    return m.group(1) if m else None

# 通过 Crossref Works API 把 DOI 解析到落地页 URL。成功返回 URL；失败返回 None
def _crossref_resolve_landing_from_doi(doi: str):

    try:
        r = SESSION.get(f"https://api.crossref.org/works/{doi}",
                        timeout=REQ_TIMEOUT)
        if r.ok:
            msg = r.json().get("message", {})
            return msg.get("URL")
    except Exception:
        pass
    return None

# 对 doi.org 做一次 HEAD 跟随重定向，拿到最终落地页。成功返回最终 URL；失败返回 None。
def _doi_head_follow(url: str):

    try:
        r = SESSION.head(url, allow_redirects=True, timeout=REQ_TIMEOUT)
        if r.ok:
            return r.url
    except Exception:
        pass
    return None

# 仅用于“抓取IEEE摘要”的解析函数：若是 IEEE 的 doi.org 链接，尽量解析到 ieeexplore 落地页。解析失败则返回原始 URL。
def resolve_ieee_scrape_url(raw_url: str):

    if not raw_url:
        return raw_url

    lower = raw_url.lower()
    if "ieeexplore.ieee.org" in lower:
        return raw_url  # 已经是落地页

    if "doi.org/10.1109" in lower:
        doi = _extract_doi(raw_url)
        # 1) 优先 Crossref 解析
        url = _crossref_resolve_landing_from_doi(doi) if doi else None
        if url and "ieeexplore.ieee.org" in url.lower():
            return url
        # 2) 退化：HEAD 跟随重定向
        url = _doi_head_follow(raw_url)
        if url:
            return url

    return raw_url  # 兜底：交给抽取函数自行处理

# 仅用于“抓取ACM摘要”的解析函数：若是 ACM 的 doi.org 链接，尽量解析到 ACM digital Library 落地页。解析失败则返回原始 URL。
def resolve_acm_scrape_url(raw_url: str):

    if not raw_url:
        return raw_url

    lower = raw_url.lower()
    if "dl.acm.org/doi/10.1145" in lower:
        return raw_url  # 已是落地页

    if "doi.org/10.1145" in lower:
        doi = _extract_doi(raw_url)
        # 1) Crossref 解析
        url = _crossref_resolve_landing_from_doi(doi) if doi else None
        if url and "dl.acm.org/doi/10.1145" in (url or "").lower():
            return url
        # 2) 退化：HEAD
        url = _doi_head_follow(raw_url)
        if url:
            return url

    return raw_url

# =============================
# 数据源：arXiv（直接提供摘要）
# =============================

# 从 arXiv API 拉取记录，逐条生成 record。
def get_arxiv_records(searchText, createdTime):

    url = "http://export.arxiv.org/api/query?"
    params = {
        # "search_query": f"all:{searchText} AND lastUpdatedDate:[{createdTime.replace("-", "")}0000 TO {createdTime.replace("-", "")}2359]",
        "search_query": f"lastUpdatedDate:[{createdTime.replace("-", "")}0000 TO {createdTime.replace("-", "")}2359]",
        "sortBy": "relevance",
        "sortOrder": "descending",
        "max_results": arXivCount,
    }

    try:
        r = SESSION.get(url, params=params, timeout=REQ_TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        print(f"arXiv 请求失败: {e}")
        return

    feed = feedparser.parse(r.text)

    for entry in feed.entries:
        indexDate = entry.updated[:10]
        title = " ".join(entry.title.split())
        authors = ", ".join(author.name for author in entry.authors)
        publish = "arXiv"
        page_url = next((link.href for link in entry.links if link.type == "text/html"), "N/A")
        summary = " ".join(entry.summary.split())

        record = {
            "date": indexDate,
            "title": title,
            "authors": authors,
            "publish": publish,
            "url": page_url,
            "source": "arXiv",
            "abstract": summary,
        }

        print(f"[arXiv] {indexDate} | {title}")
        yield record


# =============================
# 数据源：Crossref -> ACM/IEEE（需要抓取摘要）
# =============================

# 通过 Crossref 检索 ACM/IEEE，调用对应方法抓取摘要，逐条生成 record。
def get_crossref_ieee_acm_records(searchText, createdTime):

    url = "https://api.crossref.org/works"
    params = {
        # "query": searchText,
        "sort": "relevance",
        "order": "desc",
        "rows": crossrefCount,
        "select": "created,title,author,container-title,URL",
        "filter": f"prefix:10.1145,prefix:10.1109,from-created-date:{createdTime}",
        "mailto": "1424057661@qq.com",
    }

    try:
        r = SESSION.get(url, params=params, timeout=REQ_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Crossref 请求失败: {e}")
        return

    items = data.get("message", {}).get("items", [])

    for i, item in enumerate(items, start=1):
        title = item.get("title", [""])[0]
        authors_str = (
            ", ".join(
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in item.get("author", [])
            )
            if item.get("author")
            else "N/A"
        )
        publish = item.get("container-title", [""])[0] if item.get("container-title") else "N/A"
        raw_url = item.get("URL", "N/A")

        created = item.get("created", {}).get("date-parts", [])
        indexDate = "-".join(str(x) for x in created[0]) if created and created[0] else "N/A"

        source = guess_source(raw_url)

        abstract_text = ""
        try:
            # 仅“抓取摘要”时解析为落地页，落盘仍写 raw_url
            if source == "ACM":
                scrape_url = resolve_acm_scrape_url(raw_url)
                abstract_text = getAbstractFromACM(scrape_url)
            elif source == "IEEE":
                scrape_url = resolve_ieee_scrape_url(raw_url)
                abstract_text = getAbstractFromIEEE(scrape_url)
            else:
                abstract_text = ""
        except Exception as e:
            # 报错兜底：带来源与错误信息
            abstract_text = f"抓取摘要失败: {e}"

        record = {
            "date": indexDate,
            "title": title,
            "authors": authors_str,
            "publish": publish,
            "url": raw_url,      # 保持原始 URL，不做替换
            "source": source,
            "abstract": abstract_text,
        }

        print(f"[{source}] {indexDate} | {title}")
        yield record


# =============================
# 统一获取论文
# =============================

# 获取ArXiv、ACM、IEEE论文题目、作者、出版期刊/会议、URL、来源、摘要并存在到json文件。
def getAllPapers(searchText, createdTime):
    out_path = f"papers/paper{createdTime}.json"
    results = []

    def maybe_flush(force=False):
        if force or (len(results) % chunk_size == 0 and len(results) > 0):
            checkpoint_write(out_path, results)

    for rec in get_arxiv_records(searchText, createdTime):
        results.append(rec)
        maybe_flush()

    for rec in get_crossref_ieee_acm_records(searchText ,createdTime):
        results.append(rec)
        maybe_flush()

    maybe_flush(force=True)
    print(f"共写入 {len(results)} 条记录，保存到 {out_path}。")
    return out_path


# =============================
# 脚本入口
# =============================
# getAllPapers(searchText)





