# -*- coding:utf-8 -*-
import requests
import re
import json
import time

def get_one_page(url):
    '''
    该函数接收一个 url 作为参数，返回指定 url 页面的源代码。
    :param url:页面的链接
    '''
    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
    }
    response = requests.get(url,headers = headers,timeout = 5)
    # 判断响应体的状态码，若是200则表示响应成功，返回页面源代码，否则返回 None
    if response.status_code == 200:
        return response.text
    return None

def parse_one_page(html):
    '''
    该函数使用正则表达式提取一部电影的 排名、电影图片、电影名称、主演、上映时间、评分

    '''
    # 使用 compile 方法将正则字符串编译成正则表达式对象，以便在后面的匹配中复用
    pattern = re.compile('<dd>.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?name"><a'
                         + '.*?>(.*?)</a>.*?star">(.*?)</p>.*?releasetime">(.*?)</p>'
                         + '.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?</dd>', re.S)
    items = re.findall(pattern, html)
    for item in items:
        yield {
            'index': item[0],
            'image': item[1],
            'title': item[2],
            'actor': item[3].strip()[3:],
            'time': item[4].strip()[5:],
            'score': item[5] + item[6]
        }

def write_to_file(content):
    '''
    该函数用于将一部电影的信息写入到文本文件
    :param content:一部电影信息，是一个字典
    '''
    with open('result.txt', 'a', encoding='utf-8') as f:
        # 通过 JSON 库的 dumps()方法实现字典的序列化，
        # 并指定 ensure_ascii 参数为 Fasle，这样可以保证输出的结果是中文形式而不是 Unicode 编码
        f.write(json.dumps(content, ensure_ascii=False) + '\n')


def main(offset):
    url = 'http://maoyan.com/board/4?offset=' + str(offset)
    html = get_one_page(url)
    for item in parse_one_page(html):
        write_to_file(item)

for i in range(10):
    main(i*10)
    time.sleep(1)

