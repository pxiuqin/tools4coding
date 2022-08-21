# -*- coding:utf-8 -*-
# 功能：爬取一个公众号的所有历史文章存入数据库
# 用法：python wx_spider.py [公众号名称] 如python wx_spider.py xxx
import time
import random
import csv
import requests
import re
import sys
from requests.packages import urllib3
urllib3.disable_warnings()

# 全局变量
s = requests.Session()
headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0",
    "Host": "mp.weixin.qq.com",
    'Referer': 'https://mp.weixin.qq.com/'
}

# cookies 字符串，这是从浏览器中拷贝出来的字符串,略过不讲
cookie_str = "xxxxx"
cookies = {}

# 加载cookies，将字符串格式的cookies转化为字典形式
def load_cookies():
    global cookie_str, cookies
    for item in cookie_str.split(';'):
        sep_index = item.find('=')
        cookies[item[:sep_index]] = item[sep_index+1:]


def write_csv(data):

    with open('唐书房文章列表.csv', 'w', encoding='utf-8', newline='') as file_obj:
        # 1:创建writer对象
        writer = csv.writer(file_obj)

        # 2:写表头
        writer.writerow(['id', 'date', 'title', 'link'])

        # 3:遍历列表，将每一行的数据写入csv
        writer.writerows(data)

# 爬虫主函数
def spider():
    # 结果暂存
    result = []

    # 加载cookies
    load_cookies()

    # 访问官网主页
    url = 'https://mp.weixin.qq.com'
    res = s.get(url=url, headers=headers, cookies=cookies, verify=False)
    if res.status_code == 200:
        # 由于加载了cookies，相当于已经登陆了，系统作了重定义，response的url中含有我们需要的token
        print(res.url)

        # 获得token
        token = re.findall(r'.*?token=(\d+)', res.url)
        if token:
            token = token[0]
        else:  # 没有token的话，说明cookies过时了，没有登陆成功，退出程序
            print('登陆失败')
            return

        print('token', token)

        # 检索公众号
        url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz'
        data = {
            "action": "search_biz",
            "begin": "0",
            "count": "5",
            "query": sys.argv[1], 
            "token": token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1"
        }

        res = s.get(url=url, params=data, cookies=cookies,
                    headers=headers, verify=False)

        if res.status_code == 200:
            # 搜索结果的第一个往往是最准确的
            # 提取它的fakeid
            fakeid = res.json()['list'][0]['fakeid']
            print('fakeid', fakeid)

            page_size = 5
            page_count = 1
            cur_page = 1

            # 分页请求文章列表
            while cur_page <= page_count:
                if cur_page < 19:
                    continue
                time.sleep(random.randint(1,10))
                url = 'https://mp.weixin.qq.com/cgi-bin/appmsg'
                data = {
                    "action": "list_ex",
                    "begin": str(page_size*(cur_page-1)),
                    "count": str(page_size),
                    "fakeid": fakeid,
                    "type": "9",
                    "query": "",
                    "token": token,
                    "lang": "zh_CN",
                    "f": "json",
                    "ajax": "1"
                }
                res = s.get(url=url, params=data, cookies=cookies,
                            headers=headers, verify=False)
                if res.status_code == 200:
                    # print(res.json())
                    print('cur_page', cur_page)

                    try:
                        # 文章列表位于app_msg_list字段中
                        app_msg_list = res.json()['app_msg_list']
                        for item in app_msg_list:
                            # 通过更新时间戳获得文章的发布日期
                            item['post_date'] = time.strftime(
                                "%Y-%m-%d", time.localtime(int(item['update_time'])))
                            
                            # 暂存结果
                            result.append(
                                [item['aid'], item['post_date'], item['title'], item['link']])

                            print(item['post_date'], item['title'])
                    except: 
                        print("get app_msg_list error！")
                        print(res.json())

                    if cur_page == 1:  # 若是第1页，计算总的分页数
                        # 总的日期数，每page_size天的文章为一页
                        app_msg_cnt = res.json()['app_msg_cnt']
                        print('app_msg_cnt', app_msg_cnt)

                        # 计算总的分页数
                        if app_msg_cnt % page_size == 0:
                            page_count = int(app_msg_cnt / page_size)
                        else:
                            page_count = int(app_msg_cnt / page_size) + 1

                # 当前页面数+1
                cur_page += 1

            write_csv(result)

            print('完成！')


spider()
