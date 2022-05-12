import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse, quote, quote_plus
import io
import time
import os
import threading
import argparse

headers = {      
    "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-GB,en;q=0.9",
}


all_images = {}

thread_limit = 0 # don't change this

def get_extension(url):
    path = urlparse(url).path.strip('/')
    path,filename = os.path.split(path)
    filename,ext = os.path.splitext(filename)
    if ext:
        return ext
    else:
        return '.jpg'
    

def threaded_download(savepath,url):
    global thread_limit    
    print(url)
    r = requests.get(url,headers=headers)
    if r.status_code==200:
        if 'image' in r.headers.get('content-type',''):
            with open(savepath,'wb',) as f:
                f.write(r.content)
        else:
            print("Skipped "+url+" invalid content type.")
            
    elif r.status_code==404:
        print("Skipped "+url+" 404 not found.")
    else:
        print("Skipped "+url+" invalid response code.")
        
    thread_limit-=1 


def collect_images_from_google(query):
    chunk = 0
    step = 0
    prev_len = 0
    no_more = 0
    
    while True:
        r = requests.get(f'https://www.google.com/search?q={query}&tbm=isch&biw=1271&bih=697&async=_id:islrg_c,_fmt:json&asearch=ichunklite&ved=0ahUKEwjw_KTXkM_3AhVJxDgGHR-pDeoQtDIIPSgA&start={chunk}&ijn={step}',headers=headers)
        
        if r.status_code==200:
            json_text = r.content.decode('utf8').removeprefix(")]}'")
            json_data = json.loads(json_text)
            try:
                results = json_data['ichunklite']['results']
                for result in results:
                    original_image = result['viewer_metadata']['original_image']['url']
                    all_images[original_image] = result['image_docid']
            except:
                pass
                
            chunk +=100
            step +=1   
        
        if no_more>5:
            break
        if prev_len==len(all_images):
            no_more+=1
        else:
            print(len(all_images))
            prev_len = len(all_images)
            no_more = 0
       
def download_images(query):   
    global thread_limit
    print("Downloading "+str(len(all_images))+" images")
    if not os.path.exists(os.path.join("Images",f"{query}")):
        os.makedirs(os.path.join("Images",f"{query}"))
      
    for image_link,doc_id in all_images.items():  
        image_save_path = os.path.join("Images",f"{query}",doc_id+get_extension(image_link))   
        if os.path.exists(image_save_path):
            if os.path.getsize(image_save_path)>1:
                continue     
        threading.Thread(target=threaded_download,kwargs={'url':image_link,'savepath':image_save_path}).start()  
        thread_limit+=1
        while thread_limit>9:
            time.sleep(1)

    while thread_limit>0:
        time.sleep(1)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description = "Download images from google")
    parser.add_argument("-k", "--keyword", help = "Example: Help argument", required = True, default = "")
    arguments = parser.parse_args()
    keyword= arguments.keyword
    
    collect_images_from_google(keyword)
    download_images(keyword)
    
    
    
    