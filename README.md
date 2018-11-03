# 抓取猫眼电影排行

利用requests库和正则表达式来抓取猫眼电影TOP100的相关内容。


### 1.本节目标
提取出猫眼电影TOP100的电影名称、时间、评分、图片等信息，提取的站点URL为 http://maoyan.com/board/4
提取的结果会以文件形式保存下来。

### 2.准备工作
确保已正确安装了 requests 库。

### 3.抓取分析
打开需要抓取的站点，可以查看到榜单信息，如图M1所示：
![M1-榜单信息](/images/M1-榜单信息.png)
排名第一的电影是霸王别姬，页面中显示的有效信息有影片名称、主演、上映时间、上映地区、评分、图片等信息。
将网页滚动到最下方，可以发现有分页的列表，直接点击第2页、第3页，观察页面的URL和内容发生了怎样的变化，如图M2所示。
![M2-页面URL变化.png](/images/M2-页面URL变化.png)
第1页：http://maoyan.com/board/4
第2页：http://maoyan.com/board/4?offset=10
第3页：http://maoyan.com/board/4?offset=20
第4页：http://maoyan.com/board/4?offset=30

从第2页开始，比之前的URL多了一个参数，那就是 offset ，初步推断这是一个偏移量的参数。
由此可以总结出规律，offset 代表偏移量，如果偏移量是 n ，则显示的电影序号就是 n+1 到 n+10，每页显示10个。所以想获取TOP100
的电影，只需要分开请求10次，而10次的 offset 参数分别设置设置为 0、10、20···90 即可，这样获取不同的页面之后，再用正则表达式提取出
相关的信息，就可以得到TOP100的所有电影信息了。

### 4.抓取首页
接下来用代码实现这个过程。
首先抓取第一页的内容。我们实现了get_one_page()方法，并给它传入 url 参数。然后将抓取的页面结果返回，再通过 main() 方法调用。初步代码实现如下：
```
# -*- coding:utf-8 -*-
import requests

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

def main():
    url = 'http://maoyan.com/board/4'
    html = get_one_page(url)
    print(html)

main()
```

这样运行之后，就可以成功获取首页的源代码了。获取源代码后，就需要解析页面，提取出我们想要的信息。


### 5. 正则提取

接下来，回到网页看一下页面的真实源代码。在开发者模式下的 Network 监听组件中查看源代码，如图 M3-源代码 所示。
![M3-源代码](/images/M3-源代码.png)

注意，这里不要在 Elements 选项卡中直接查看源代码，因为那里的源码可能经过 JavaScript 操作而与原始请求不同，而是需要从 Network 选项卡部分查看原始请求得到的源码。

可以看到，一部电影信息对应的源代码是一个 dd 节点，我们利用正则表达式来提取这里面的一些电影信息。首先，需要提取它的排名信息。
而它的排名信息是在 class 为 board-index 的 i 节点内，这里利用非贪婪匹配来提取 i 节点内的信息，正则表达式写为：
```
<dd>.*?board-index.*?>(.*?)</i>
```

随后需要提取电影的图片。可以看到，后面有 a 节点，其内部有两个 img 节点。经过检查后发现，第二个 img 节点的 data-src 属性为图片链接，
这里提取第二个 img 节点的 data-src 属性，正则表达式改写如下：
```
<dd>.*?board-index.*?>(.*?)</i>.*?src="(.*?)"
```

再往后，需要提取电影的名称，它在后面的 p 节点内，class 为 name。所以，可以用 name 做一个标志位，然后进一步提取到其内 a 节点的正文内容，此时正则表达式改写如下：
```
<dd>.*?board-index.*?>(.*?)</i>.*?src="(.*?)".*?name.*?a.*?>(.*?)</a>
```

再提取主演、发布时间、评分等内容时，都是同样的原理。最后，正则表达式写为：
```
<dd>.*?board-index.*?>(.*?)</i>.*?src="(.*?)".*?name.*?a.*?>(.*?)</a>.*?star.*?>(.*?)</p>.*?releasetime.*?>(.*?)</p>.*?integer.*?>(.*?)</i>.*?fraction.*?>(.*?)</i>.*?</dd>
```

这样一个正则表达式可以匹配一个电影的结果，里面匹配了7个信息。
接下来，通过调用 findeall() 方法提取出所有的内容。

接下来，我们再定义解析页面的方法 parse_one_page()，主要是通过正则表达式来从结果中提取出我们想要的内容，实现代码如下：
```
def parse_one_page(html):
    '''
    该函数使用正则表达式提取一部电影的 排名、电影图片、电影名称、主演、上映时间、评分
    '''
    # 使用 compile 方法将正则字符串编译成正则表达式对象，以便在后面的匹配中复用
    pattern = re.compile('<dd>.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?name"><a'
                         + '.*?>(.*?)</a>.*?star">(.*?)</p>.*?releasetime">(.*?)</p>'
                         + '.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?</dd>', re.S)
    items = re.findall(pattern, html)
    print(items)
```

这样就可以成功的将一页的 10 个电影信息都提取出来，这是一个列表形式，输出结果如下：
```
[('1', 'http://p1.meituan.net/movie/20803f59291c47e1e116c11963ce019e68711.jpg@160w_220h_1e_1c', '霸王别姬', '\n                主演：张国荣,张丰毅,巩俐\n        ', '上映时间：1993-01-01', '9.', '6'), ('2', 'http://p0.meituan.net/movie/283292171619cdfd5b240c8fd093f1eb255670.jpg@160w_220h_1e_1c', '肖申克的救赎', '\n                主演：蒂姆·罗宾斯,摩根·弗里曼,鲍勃·冈顿\n        ', '上映时间：1994-10-14(美国)', '9.', '5'), ('3', 'http://p0.meituan.net/movie/54617769d96807e4d81804284ffe2a27239007.jpg@160w_220h_1e_1c', '罗马假日', '\n                主演：格利高里·派克,奥黛丽·赫本,埃迪·艾伯特\n        ', '上映时间：1953-09-02(美国)', '9.', '1'), ('4', 'http://p0.meituan.net/movie/e55ec5d18ccc83ba7db68caae54f165f95924.jpg@160w_220h_1e_1c', '这个杀手不太冷', '\n                主演：让·雷诺,加里·奥德曼,娜塔莉·波特曼\n        ', '上映时间：1994-09-14(法国)', '9.', '5'), ('5', 'http://p1.meituan.net/movie/f5a924f362f050881f2b8f82e852747c118515.jpg@160w_220h_1e_1c', '教父', '\n                主演：马龙·白兰度,阿尔·帕西诺,詹姆斯·肯恩\n        ', '上映时间：1972-03-24(美国)', '9.', '3'), ('6', 'http://p1.meituan.net/movie/0699ac97c82cf01638aa5023562d6134351277.jpg@160w_220h_1e_1c', '泰坦尼克号', '\n                主演：莱昂纳多·迪卡普里奥,凯特·温丝莱特,比利·赞恩\n        ', '上映时间：1998-04-03', '9.', '5'), ('7', 'http://p0.meituan.net/movie/da64660f82b98cdc1b8a3804e69609e041108.jpg@160w_220h_1e_1c', '唐伯虎点秋香', '\n                主演：周星驰,巩俐,郑佩佩\n        ', '上映时间：1993-07-01(中国香港)', '9.', '2'), ('8', 'http://p0.meituan.net/movie/b076ce63e9860ecf1ee9839badee5228329384.jpg@160w_220h_1e_1c', '千与千寻', '\n                主演：柊瑠美,入野自由,夏木真理\n        ', '上映时间：2001-07-20(日本)', '9.', '3'), ('9', 'http://p0.meituan.net/movie/46c29a8b8d8424bdda7715e6fd779c66235684.jpg@160w_220h_1e_1c', '魂断蓝桥', '\n                主演：费雯·丽,罗伯特·泰勒,露塞尔·沃特森\n        ', '上映时间：1940-05-17(美国)', '9.', '2'), ('10', 'http://p0.meituan.net/movie/230e71d398e0c54730d58dc4bb6e4cca51662.jpg@160w_220h_1e_1c', '乱世佳人', '\n                主演：费雯·丽,克拉克·盖博,奥利维娅·德哈维兰\n        ', '上映时间：1939-12-15(美国)', '9.', '1')]
[Finished in 0.6s]

```

但这样还不够，数据比较杂乱，我们再将匹配结果处理一下，遍历提取结果并生成字段，此时改写如下：
```
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

def main():
    url = 'http://maoyan.com/board/4'
    html = get_one_page(url)
    for item in parse_one_page(html):
        print(item)

main()

```

这样就可以成功提取出电影的排名、图片、标题、主演、时间、评分，并把它赋值为一个个字典，形成结构化数据。运行结果如下：
```
{'index': '1', 'image': 'http://p1.meituan.net/movie/20803f59291c47e1e116c11963ce019e68711.jpg@160w_220h_1e_1c', 'title': '霸王别姬', 'actor': '张国荣,张丰毅,巩俐', 'time': '1993-01-01', 'score': '9.6'}
{'index': '2', 'image': 'http://p0.meituan.net/movie/283292171619cdfd5b240c8fd093f1eb255670.jpg@160w_220h_1e_1c', 'title': '肖申克的救赎', 'actor': '蒂姆·罗宾斯,摩根·弗里曼,鲍勃·冈顿', 'time': '1994-10-14(美国)', 'score': '9.5'}
{'index': '3', 'image': 'http://p0.meituan.net/movie/54617769d96807e4d81804284ffe2a27239007.jpg@160w_220h_1e_1c', 'title': '罗马假日', 'actor': '格利高里·派克,奥黛丽·赫本,埃迪·艾伯特', 'time': '1953-09-02(美国)', 'score': '9.1'}
{'index': '4', 'image': 'http://p0.meituan.net/movie/e55ec5d18ccc83ba7db68caae54f165f95924.jpg@160w_220h_1e_1c', 'title': '这个杀手不太冷', 'actor': '让·雷诺,加里·奥德曼,娜塔莉·波特曼', 'time': '1994-09-14(法国)', 'score': '9.5'}
{'index': '5', 'image': 'http://p1.meituan.net/movie/f5a924f362f050881f2b8f82e852747c118515.jpg@160w_220h_1e_1c', 'title': '教父', 'actor': '马龙·白兰度,阿尔·帕西诺,詹姆斯·肯恩', 'time': '1972-03-24(美国)', 'score': '9.3'}
{'index': '6', 'image': 'http://p1.meituan.net/movie/0699ac97c82cf01638aa5023562d6134351277.jpg@160w_220h_1e_1c', 'title': '泰坦尼克号', 'actor': '莱昂纳多·迪卡普里奥,凯特·温丝莱特,比利·赞恩', 'time': '1998-04-03', 'score': '9.5'}
{'index': '7', 'image': 'http://p0.meituan.net/movie/da64660f82b98cdc1b8a3804e69609e041108.jpg@160w_220h_1e_1c', 'title': '唐伯虎点秋香', 'actor': '周星驰,巩俐,郑佩佩', 'time': '1993-07-01(中国香港)', 'score': '9.2'}
{'index': '8', 'image': 'http://p0.meituan.net/movie/b076ce63e9860ecf1ee9839badee5228329384.jpg@160w_220h_1e_1c', 'title': '千与千寻', 'actor': '柊瑠美,入野自由,夏木真理', 'time': '2001-07-20(日本)', 'score': '9.3'}
{'index': '9', 'image': 'http://p0.meituan.net/movie/46c29a8b8d8424bdda7715e6fd779c66235684.jpg@160w_220h_1e_1c', 'title': '魂断蓝桥', 'actor': '费雯·丽,罗伯特·泰勒,露塞尔·沃特森', 'time': '1940-05-17(美国)', 'score': '9.2'}
{'index': '10', 'image': 'http://p0.meituan.net/movie/230e71d398e0c54730d58dc4bb6e4cca51662.jpg@160w_220h_1e_1c', 'title': '乱世佳人', 'actor': '费雯·丽,克拉克·盖博,奥利维娅·德哈维兰', 'time': '1939-12-15(美国)', 'score': '9.1'}
```

到此为止，我们就成功提取了单页的电影信息。


### 6.写入文件
随后，我们将提取的结果写入文件，这里直接写入到一个文本文件中。这里通过 JSON 库的 dumps()方法实现字典的序列化，并指定 ensure_ascii 参数为 Fasle，这样可以保证输出的结果是中文形式而不是 Unicode 编码。代码如下：
```
def write_to_file(content):
    with open('result.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')
```

通过调用 write_to_file() 方法即可将字典写入到文本文件的过程，此处的 content 参数就是一部电影的提取结果，是一个字典。

### 7.整合代码
最后，实现 main() 方法来调用前面实现的方法，将单页的电影结果写入到文件。相关的代码如下：
```
def main():
    url = 'http://maoyan.com/board/4'
    html = get_one_page(url)
    for item in parse_one_page(html):
        write_to_file(item)
```

到此为止，我们就完成了单页电影的提取，也就是首页的 10 部电影可以成功提取并保存到文本文件中了。

### 8.分页爬取
因为我们需要抓取的是 TOP100 的电影，所以还需要遍历一下，给这个链接传入 offset 参数，实现其他 90 部电影的爬取，此时添加如下调用即可：
```
def main(offset):
    url = 'http://maoyan.com/board/4?offset=' + str(offset)
    html = get_one_page(url)
    for item in parse_one_page(html):
        write_to_file(item)

for i in range(10):
    main(i*10)
```

到此为止，我们的猫眼电影 TOP100 的爬虫就全部写完了

### 9.总结
本节的代码地址为：https://github.com/cunxi1992/MaoYan
本节中，通过爬取猫眼 TOP100 的电影信息练习了 requests 和正则表达式的用法。这是一个最基础的实例。



