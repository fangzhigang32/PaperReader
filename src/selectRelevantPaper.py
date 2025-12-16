# 从json文件中选择和自己相关的论文，并把标题和摘要翻译为中文后发送邮件

import os
import json
import html
from datetime import date
from setLLM import ChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========== 可配置参数 ==========
chunk_size = 10
createdTime = date.today().strftime("%Y-%m-%d")

# 邮件配置（请改为你自己的账号或使用环境变量）
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_PASS  = os.environ.get('SENDER_PASS')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.qq.com')
SMTP_PORT = os.environ.get('SMTP_PORT', 465)
BROAD_FIELD = os.environ.get('BROAD_FIELD',"AI for Electronic Design Automation (EDA)")
SPECIFIC_FIELD = os.environ.get('SPECIFIC_FIELD',"").split(',')

# ========== 工具函数 ==========
def _checkpoint_write(path, data):
    """覆盖写入 JSON 文件"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _safe_get(paper, key, default=""):
    """安全获取字典值，用于非HTML场景（如LLM输入）"""
    v = paper.get(key, default)
    return "" if v is None else v

def _safe_get_escaped(data, key, default='None'):
    """安全获取字典值并进行HTML转义，用于HTML输出防止XSS"""
    value = data.get(key, default) if isinstance(data, dict) else default
    return html.escape(str(value)) if value else html.escape(default)

# ========== LLM 调用 ==========
def llm_is_relevant(title, abstract, broad_field="AI for Electronic Design Automation (EDA)", specific_field=None):
    """判断论文是否与研究方向相关"""
    if not (title or abstract):
        return False
    
    # Electronic Design Automation (EDA) and Large Language Model (LLM)-assisted chip design
    # code generation, static code analysis, lint violation detection and repair, coding standard violations, and security vulnerabilities

    system_template = "You are an academic assistant who helps users filter papers related to their research interests."
    struct_specific_field = ", ".join(specific_field) if specific_field else "various subfields"
    user_template = (
        "My research focuses on {broad_field};\n\n"
        "My specific research subfield is: {struct_specific_field}. \n\n"
        "Please evaluate whether the following paper aligns with my research direction by considering the paper's research question, core concepts and keywords, methods and technical approach, and main contributions and conclusions. If the paper's core problem and primary contributions fall directly within my specific research subfield, or if it has clear and direct research value for this subfield (rather than being only broadly related at the broad-field level), then judge it as 'aligned'. If it is only related at the broad-field level, has a weak/indirect connection to the specific subfield, or its topic and contributions clearly do not match, then judge it as 'not aligned' \n\n"
        "After careful reasoning, provide your final conclusion at the end: if it aligns, please answer 'My conclusion is Yes'; if it does not align, please answer 'My conclusion is No'."
        "Paper Title: {title} \n\nPaper Abstract: {abstract}"
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("user", user_template)
    ])

    output_parser = StrOutputParser()
    chain = prompt_template | ChatModel | output_parser
    
    try:
        res = chain.invoke({"title": title or "No Title", "abstract": abstract or "No Abstract", "broad_field": broad_field, "struct_specific_field": struct_specific_field})
        if 'MY CONCLUSION IS' in res.upper():
            result = res.strip().upper().split("MY CONCLUSION IS")[1].strip()
        else:
            result = res.strip().upper()
        return "YES" in result
    except Exception as e:
        print("判定相关性时出错：", e)
        return False

def llm_translate_to_zh(text):
    """将英文文本翻译为中文"""
    if not text:
        return "None"

    system_template = "You are an experienced translator who can translate English into Chinese. If the input is empty, output 'None'."
    user_template = "{text}"

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("user", user_template)
    ])

    output_parser = StrOutputParser()
    chain = prompt_template | ChatModel | output_parser

    try:
        res = chain.invoke({"text": text})
        return (res or "").strip() or "None"
    except Exception as e:
        print("翻译时出错：", e)
        return "None"

# ========== 主流程 ==========
def select_translate_and_save(file_path):
    """筛选相关论文并翻译标题和摘要"""
    dir_name, base_name = os.path.split(file_path)
    out_path = f"papers/select_{base_name}"


    with open(file_path, 'r', encoding='utf-8') as f:
        papers = json.load(f)

    yes_results = []
    total = len(papers)
    yes_cnt = 0

    for idx, paper in enumerate(papers, start=1):
        title = _safe_get(paper, 'title', 'No Title')
        abstract = _safe_get(paper, 'abstract', 'No Abstract')        

        is_rel = llm_is_relevant(title, abstract, BROAD_FIELD, SPECIFIC_FIELD)
        tag = "YES" if is_rel else "NO"

        if is_rel:
            yes_cnt += 1
            # 翻译标题和摘要
            title_zh = llm_translate_to_zh(title)
            abstract_zh = llm_translate_to_zh(abstract)

            paper_with_zh = dict(paper)
            paper_with_zh["title_zh"] = title_zh
            paper_with_zh["abstract_zh"] = abstract_zh
            yes_results.append(paper_with_zh)

            if len(yes_results) % chunk_size == 0 or idx == total:
                _checkpoint_write(out_path, yes_results)

        print(f"[{tag}] {idx}/{total} | {title}")

    _checkpoint_write(out_path, yes_results)
    print(f"筛选完成：共 {total} 篇；Yes = {yes_cnt} 篇；已保存到 {out_path}。")
    return out_path

# ========== 邮件发送 ==========
def send_email(sender_email, sender_password, receiver_email, subject, body, smtp_server, smtp_port=465):
    """发送邮件"""
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html', 'utf-8'))

    server = None
    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        print("邮件发送成功！")
    except smtplib.SMTPServerDisconnected as e:
        print("邮件已发送，但服务器提前断开连接：", e)
    except smtplib.SMTPAuthenticationError as e:
        print("登录失败：请检查邮箱账号或授权码是否正确。", e)
    except smtplib.SMTPRecipientsRefused as e:
        print("收件人地址被拒绝，请检查邮箱是否存在。", e)
    except Exception as e:
        print("邮件发送失败：", e)
    finally:
        if server:
            server.quit()

def build_email_body_from_selected(selected_file_path):
    """构造邮件正文（包含中英文标题与摘要，优化HTML格式）"""
    try:
        with open(selected_file_path, 'r', encoding='utf-8') as f:
            papers = json.load(f)
    except Exception as e:
        return f"<p>读取论文文件失败：{html.escape(str(e))}</p>"

    if not papers or not isinstance(papers, list):
        return """
        <div style="font-family: Arial, 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #333;">
            <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px;">论文筛选结果</h3>
            <p style="font-size: 16px; color: #666;">本次未筛选到与研究方向相关的论文。</p>
        </div>
        """

    # 构建HTML正文
    body_html = """
    <div style="font-family: Arial, 'Microsoft YaHei', sans-serif; line-height: 1.8; color: #333; max-width: 1000px; margin: 0 auto;">
        <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 20px 0;">
    """

    for idx, paper in enumerate(papers, start=1):
        # 安全获取各项信息（已转义）
        title = _safe_get_escaped(paper, 'title', 'No Title')
        title_zh = _safe_get_escaped(paper, 'title_zh', 'None')
        authors = _safe_get_escaped(paper, 'authors', 'No Authors')
        publish = _safe_get_escaped(paper, 'publish', 'No Publish')
        source = _safe_get_escaped(paper, 'source', 'No Source')
        abstract = _safe_get_escaped(paper, 'abstract', 'No Abstract')
        abstract_zh = _safe_get_escaped(paper, 'abstract_zh', 'None')
        # URL 需要特殊处理：href 属性用原值，显示文本需转义
        url_raw = paper.get('url', 'No URL') if isinstance(paper, dict) else 'No URL'
        url_display = html.escape(str(url_raw)) if url_raw else 'No URL'

        # 单个论文卡片
        paper_card = f"""
        <div style="background: #f8f9fa; border-radius: 8px; padding: 25px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <h3 style="color: #3498db; margin-top: 0; margin-bottom: 20px; font-size: 20px;">
                论文 {idx}
                <span style="font-size: 14px; color: #7f8c8d; font-weight: normal; margin-left: 10px;">
                    ({source})
                </span>
            </h3>
            
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                <tr style="background: #e9ecef;">
                    <th style="padding: 10px; text-align: left; width: 120px; color: #2c3e50; font-weight: 600; border: 1px solid #dee2e6;">
                        标题（英文）
                    </th>
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-size: 15px;">
                        {title}
                    </td>
                </tr>
                <tr>
                    <th style="padding: 10px; text-align: left; color: #2c3e50; font-weight: 600; border: 1px solid #dee2e6;">
                        标题（中文）
                    </th>
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-size: 15px; color: #555;">
                        {title_zh}
                    </td>
                </tr>
                <tr style="background: #e9ecef;">
                    <th style="padding: 10px; text-align: left; color: #2c3e50; font-weight: 600; border: 1px solid #dee2e6;">
                        作者
                    </th>
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-size: 14px;">
                        {authors}
                    </td>
                </tr>
                <tr>
                    <th style="padding: 10px; text-align: left; color: #2c3e50; font-weight: 600; border: 1px solid #dee2e6;">
                        发表信息
                    </th>
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-size: 14px; color: #666;">
                        {publish}
                    </td>
                </tr>
                <tr style="background: #e9ecef;">
                    <th style="padding: 10px; text-align: left; color: #2c3e50; font-weight: 600; border: 1px solid #dee2e6;">
                        原文链接
                    </th>
                    <td style="padding: 10px; border: 1px solid #dee2e6; font-size: 14px;">
                        <a href="{url_raw}" style="color: #3498db; text-decoration: none;" target="_blank">
                            {url_display if len(url_display) <= 50 else url_display[:50] + '...'}
                        </a>
                    </td>
                </tr>
            </table>

            <div style="margin-top: 20px;">
                <h4 style="color: #2c3e50; margin-bottom: 8px; font-size: 16px;">摘要（英文）</h4>
                <div style="background: #ffffff; padding: 12px; border-radius: 4px; border-left: 3px solid #3498db; font-size: 14px; line-height: 1.7; color: #444;">
                    {abstract}
                </div>
            </div>

            <div style="margin-top: 15px;">
                <h4 style="color: #2c3e50; margin-bottom: 8px; font-size: 16px;">摘要（中文）</h4>
                <div style="background: #ffffff; padding: 12px; border-radius: 4px; border-left: 3px solid #2ecc71; font-size: 14px; line-height: 1.7; color: #444;">
                    {abstract_zh}
                </div>
            </div>
        </div>
        """
        body_html += paper_card

    # 结尾信息
    body_html += """
        <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 30px 0;">
        <div style="text-align: center; font-size: 13px; color: #7f8c8d;">
            <p>本邮件由系统自动生成，如有疑问请联系相关负责人</p>
        </div>
    </div>
    """

    return body_html

def select_translate_and_email(file_path):
    """一键执行筛选、翻译、邮件发送"""
    selected_path = select_translate_and_save(file_path)
    body = build_email_body_from_selected(selected_path)
    send_email(
        sender_email=SENDER_EMAIL,
        sender_password=SENDER_PASS,
        receiver_email=RECEIVER_EMAIL,
        subject=f"{createdTime} 论文推送",
        body=body,
        smtp_server=SMTP_SERVER,
        smtp_port=SMTP_PORT
    )

def select_error_message_email(ErrorMessage):
    """发送错误通知邮件"""
    send_email(
        sender_email=SENDER_EMAIL,
        sender_password=SENDER_PASS,
        receiver_email=RECEIVER_EMAIL,
        subject=f"{createdTime} 论文推送",
        body="本次论文筛选出现错误，请检查相关代码或日志。\n"+str(ErrorMessage),
        smtp_server=SMTP_SERVER,
        smtp_port=SMTP_PORT
    )

