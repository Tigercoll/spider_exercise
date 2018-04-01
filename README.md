# spider_exercise
学习爬虫阶段的各种练习代码。
#### 爬虫练习模拟登陆知乎

出于练习目的，看网上大家都在爬取知乎，所以就打算自己试试手，但是发现改版后的知乎登陆难度貌似加大的不少。参考大神分析的分析思路，大概写了一个。环境是python3下的，用到的库有：requests，time，re，hashlib，hmac，base64，PIL，matplotlib，json。

##### 抓包

打开抓包工具Fiddler,打开知乎首页，输入错误账号密码。

![](https://github.com/Tigercoll/my_picturelib/raw/master/login_zhihu/headers.png)

POST https://www.zhihu.com/api/v3/oauth/sign_in 为我们需要提交headers跟formdata的地址。

headers 部分，看到有 

authorization: oauth c3cef7c66a1843f8b3a9e6a1e3160e20（这个在js文件里找到了。是固定值）

X-UDID: AAAgZO3PXw2PTrQPoJUwRfnD6YVV1s22MAs=（这个好像没什么用，我没加也能登录）

X-Xsrftoken: f05f16f1-1de9-45ad-9c5d-76e122a59fb0

第一次请求还有Cookie，说明他有set_cookie 的动作，说明X-Xsrftoken 很可能在cookie里面。（这个是大神讲解的。我也不是很明白。最终发现确实在cookie里有，大神就是大神- -）所以我们要先请求一次获取报头里的_xsrf，用正则取出来。记得一定要加heades。

```python
	response = zhihu_sesssion.get(login_url,headers=headers)
    token = re.findall(r'_xsrf=([\w|-]+)', response.headers.get('Set-Cookie'))[0]
```



![](https://github.com/Tigercoll/my_picturelib/raw/master/login_zhihu/formdata.png)

client_id：跟authorization一样固定值 ，c3cef7c66a1843f8b3a9e6a1e3160e20

grant_type：类型，我们用账号密码登录就填password就好了。

timestamp：时间戳，我们用time.time()不过这里有12位，所以要乘以1000，用int取整，但是传的str类型的。

```python
timestamp = str(int(time.time() * 1000))
```

source：固定值，com.zhihu.web

signature：打开浏览器F12全局查找，找到了，在JS里面。应该是JS 生成的。不过具体怎么生成的，把这份JS拷贝出来，解析一下。（个人对JS 还是比较弱的，所以参考的大神的。）是通过 Hmac 算法对几个固定值和时间戳进行加密，那么只需要在 Python 里也模拟一次这个加密即可。

![](https://github.com/Tigercoll/my_picturelib/raw/master/login_zhihu/signature.png)

```python
    ha = hmac.new(b'd1b964811afb40118a12068ff74a12f4', digestmod=hashlib.sha1)
    grant_type ='password'
    client_id ='c3cef7c66a1843f8b3a9e6a1e3160e20'
    source = 'com.zhihu.web'
    ha.update(bytes((grant_type + client_id + source + timestamp),'utf-8'))
```

username和password就不说了。

captcha：验证码，是通过 GET 请求单独的 API 接口返回是否需要验证码（无论是否需要，都要请求一次），如果是 True 则需要再次 PUT 请求获取图片的 base64 编码。

![](https://github.com/Tigercoll/my_picturelib/raw/master/login_zhihu/captcha_get.png)

![](https://github.com/Tigercoll/my_picturelib/raw/master/login_zhihu/captcha_put.png)

这个验证码的API 是单独的，所以需要先post到验证的url上，然后再一起post到登录的url上。

验证码有两个一个是中文点击，一个是英文输入，（本人才疏学浅，只能了解到英文输入的，中文点击完全借鉴的大神，恩，就是抄袭。哈哈哈哈）

```python
def _get_captcha(zhihu_sesssion,headers):
    '''
    获取验证码信息
    :return:
    '''
    lang = headers.get('lang', 'en')
    if lang == 'cn':
        api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=cn'
    else:
        api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
    resp = zhihu_sesssion.get(api, headers=headers)
    show_captcha = re.search(r'true', resp.text)
    if show_captcha:
        put_resp = zhihu_sesssion.put(api, headers=headers)
        img_base64 = re.findall(
            r'"img_base64":"(.+)"', put_resp.text, re.S)[0].replace(r'\n', '')
        with open('./captcha.jpg', 'wb') as f:
            f.write(base64.b64decode(img_base64))
        img = Image.open('./captcha.jpg')
        if lang == 'cn':
            plt.imshow(img)
            print('点击所有倒立的汉字，按回车提交')
            points = plt.ginput(7)
            capt = json.dumps({'img_size': [200, 44],
                               'input_points': [[i[0] / 2, i[1] / 2] for i in points]})
        else:
            img.show()
            capt = input('请输入图片里的验证码：')
        # 这里必须先把参数 POST 验证码接口
            zhihu_sesssion.post(api, data={'input_text': capt}, headers=headers)
        return capt
    return ''
```

至此，formdata，headers全部拿到。post到‘https://www.zhihu.com/api/v3/oauth/sign_in’即可。

完整代码在我的[github](https://github.com/Tigercoll/spider_exercise)上，欢迎各位大神新手讨论批评建议。

参考文献：https://zhuanlan.zhihu.com/p/34073256                http://baijiahao.baidu.com/s?id=1590107984958781430&wfr=spider&for=pc  
