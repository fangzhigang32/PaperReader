import sys
import os
from datetime import datetime, date, timedelta
from getPaper import getAllPapers
from selectRelevantPaper import select_translate_and_email,select_error_message_email
import traceback


# 搜索关键词
searchText = os.environ.get('SEARCH_TEXT', 'AI')

# 当前日期的前一天
createdTime = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

class FileLogger:
    """只记录到文件的日志类"""
    def __init__(self, filename):
        self.terminal = sys.stdout
        # 确保日志目录存在
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        self.log_file = open(filename, 'w', encoding='utf-8')
    
    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()
    
    def flush(self):
        self.terminal.flush()
        self.log_file.flush()
    
    def close(self):
        self.log_file.close()

# 重定向标准输出和标准错误到文件
log_file = f'../runlog/{createdTime}.log'
logger = FileLogger(log_file)
# original_stdout = sys.stdout
# original_stderr = sys.stderr
sys.stdout = logger
sys.stderr = logger

try:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行论文搜索任务")
    print(f"搜索关键词: {searchText}")
    print(f"搜索日期范围: {createdTime}")
    print("正在获取论文...")
    
    path = getAllPapers(searchText, createdTime)
    
    if path:
        print(f"论文获取成功，文件路径: {path}")
        print("正在筛选、翻译并发送邮件...")
        select_translate_and_email(path)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 任务执行成功！")
    else:
        error_msg = f"论文获取失败，getAllPapers 返回空路径"
        print(f"错误: {error_msg}")
        # 发送错误邮件
        select_error_message_email(error_msg)
    
except Exception as e:
    # 捕获所有异常，包括堆栈信息
    error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    error_msg = f"任务执行失败！\n时间: {error_time}\n错误类型: {type(e).__name__}\n错误信息: {str(e)}\n\n堆栈信息:\n{traceback.format_exc()}"
    print(error_msg)
    
    # 发送错误邮件（确保即使发送邮件失败也不会影响程序退出）
    try:
        select_error_message_email(error_msg)
        print("错误邮件已发送")
    except Exception as email_error:
        print(f"发送错误邮件时发生异常: {str(email_error)}")
        print(f"邮件发送失败的堆栈信息:\n{traceback.format_exc()}")
    
finally:
    # 恢复标准输出和错误
    # sys.stdout = original_stdout
    # sys.stderr = original_stderr

    sys.stdout = logger.terminal
    sys.stderr = logger.terminal
    logger.close()
    print(f"\n日志已保存到: {log_file}")