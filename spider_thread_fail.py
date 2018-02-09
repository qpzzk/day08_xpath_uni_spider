import requests
from lxml import etree
from requests import RequestException
from w3lib.html import remove_tags
import time
from queue import Queue
import threading

url='http://140.143.192.76:8002/ranking/1528.htm'
column_queue=[]
link_queue=Queue()  #设置队列，保存url
DOWNLOADER_NUM=10   #设置了10个线程
threads=[]          #线程列表，保存Thread对象

#获取页面的内容
def get_page(url):
    global column_queue,link_queue
    response=requests.get(url)
    response.raise_for_status()
    selector=etree.HTML(response.text)
    rows=selector.xpath('//*[@id="page-wrapper"]//div[2]//div[2]//div[5]/table/tbody')
    for row in rows:
        #print(row.xpath('./tr//text()'))   #这是列表
        for column in row.xpath('./tr//text()'):
                contents=str(column).strip()  #去两边的空格
                if len(contents)!=0:   #去完空格后两边变成为0的字符串，消除
                    column_queue.append(contents)
        # for i in range(0,len(column_queue),4):  #让字符串每行四列输出
        #     print(column_queue[i:i+4])
        links=row.xpath('./tr//@href')
        for link in links:
            if str(link).startswith('http://'):
                link_queue.put(str(link))          #已经将url放入queue中，也能get出来
                # link=link_queue.get()
        print(111,"---",link_queue.queue)
        return link_queue

def filter(html):
    """过滤网页源码中的特殊符号和sup标签"""
    return remove_tags(html, which_ones=('sup',)).replace('\n', '') \
        .replace('\r', '').replace('\t', '')

#将新页面链接
def get_detail(html):
    try:
        html=filter(html)
        response=requests.get(html)
        if response.status_code==200:
            parse_page(response.text)
        return None
    except RequestException:
        return None


#将获得的页面解析
def parse_page(text):
    text=filter(text)
    s=etree.HTML(text)
    title=s.xpath('//*[@id="wikiContent"]/h1/text()')[0]
    keys=s.xpath('//*[@id="wikiContent"]/div[1]/table/tbody/tr/td[1]/p/text()')
    keys=[key.strip() for key in keys]
    values=s.xpath('//*[@id="wikiContent"]/div[1]/table/tbody/tr/td[2]')
    values=[','.join(value.xpath('.//text()')) for value in values]
    # print(title)
    # print(dict(zip(keys,values)))
    info={title:dict(zip(keys,values))}
    print(info)

def downloader():
    while True:
        get_page(url)
        print(222,"----",link_queue.queue)
        link=link_queue.get()
        print(link)
        #从队列中获得的是None，就退出循环
        if link is None:
            break
        if not str(link).startswith('http://'):
            link = 'http://%s/%s' % (url, link)
        get_detail(link)
        #执行一次就给队列发送完成任务
        link_queue.task_done()
        print('remaining queue: %s' %link_queue.qsize())



def main():
    start=time.time()
    #启动线程
    for i in range(DOWNLOADER_NUM):
        t=threading.Thread(target=downloader)
        t.start()
        threads.append(t)
    #阻塞直到队列清空为止
    link_queue.join()
    #向队列发送线程数，可以通知线程退出
    for i in range(DOWNLOADER_NUM):
        link_queue.put(None) #将None推到queue里，表示执行完线程后面给的空
    #退出线程
    for t in threads:
        t.join()
    end=time.time()
    print(end-start)


if __name__=="__main__":
    main()






