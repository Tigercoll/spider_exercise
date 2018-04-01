#!/usr/bin/env python
#_*_coding:utf-8_*_
__author__ = "Tiger"
import requests
import time
import re
import hashlib
import hmac
import base64
from PIL import Image
import matplotlib.pyplot as plt
import json
def _get_signature(timestamp):
    '''
    获取signature
    :return:
    '''
    ha = hmac.new(b'd1b964811afb40118a12068ff74a12f4', digestmod=hashlib.sha1)
    grant_type ='password'
    client_id ='c3cef7c66a1843f8b3a9e6a1e3160e20'
    source = 'com.zhihu.web'
    ha.update(bytes((grant_type + client_id + source + timestamp),'utf-8'))
    return ha.hexdigest()

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






def _get_token(zhihu_sesssion):
    login_url = 'https://www.zhihu.com/signup'
    headers = {
        'Host': 'www.zhihu.com',
        'Connection': 'keep - alive',
        'User-Agent': 'Mozilla / 5.0(WindowsNT10.0;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome/65.0.3325.162Safari/ 537.36',
        'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
    }
    resp = zhihu_sesssion.get(login_url,headers=headers)
    token = re.findall(r'_xsrf=([\w|-]+)', resp.headers.get('Set-Cookie'))[0]
    return token

def login_zhihu_spider(username,password):
    '''

    :param username: 手机号
    :param password: 密码
    :return: status 登陆是否成功
    '''
    #TODO
    zhihu_sesssion = requests.Session()
    url='https://www.zhihu.com/api/v3/oauth/sign_in'
    xsrftoken=_get_token(zhihu_sesssion)
    headers={
        'Host': 'www.zhihu.com',
        'Connection': 'keep - alive',
        'User-Agent': 'Mozilla / 5.0(WindowsNT10.0;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome/65.0.3325.162Safari/ 537.36',
        'authorization':'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
        'X-Xsrftoken': xsrftoken,
    }

    timestamp = str(int(time.time() * 1000))
    captcha=_get_captcha(zhihu_sesssion,headers)
    signature=_get_signature(timestamp)

    FORM_DATA = {
        'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
        'grant_type': 'password',
        'source': 'com.zhihu.web',
        'username': username,
        'password': password,
        # 改为'cn'是倒立汉字验证码
        'lang': 'en',
        'ref_source': 'homepage',
        'captcaha':captcha,
        'signature':signature,
        'timestamp':timestamp,
    }
    res =zhihu_sesssion.post(url,headers=headers,data=FORM_DATA)
    return headers

if __name__ =='__main__':
    username=input('请输入用户名：')
    password=input('请输入密码：')
    headers=login_zhihu_spider(username=username,password=password)
    response = requests.get('https://www.zhihu.com/people/tigercoll/activities',headers=headers )
    print(response.content)
