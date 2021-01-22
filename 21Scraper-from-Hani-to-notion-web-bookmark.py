# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.9.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

import math
import requests
import re
import time
from bs4 import BeautifulSoup

from notion.client import NotionClient
from notion.block import BookmarkBlock, TextBlock

# ---

# 준비 :
# 1. 노션에 '스크래핑 전용 페이지'를 만들어 두어야 합니다. (물론 노션 계정도 있어야 합니다.)
# 2. 라이브러리 : 노션 비공식 API인 Notion-py를 설치해야 합니다. (물론 BeautifulSoup도 설치되어 있어야 합니다) 
# 3. my_notion.py 파일을 형성해줘야 합니다. 두 줄이면 됩니다. 1행 : token = "내 노션에 들어가 받아온 토큰 값", 2행 : page = "내가 노션에 만들어둔 스크래핑 전용 페이지". 문자열로 적어주시면 됩니다. 개인정보니만큼 비밀로 하셔야 하고요, 특히 토큰 값은 노출되지 않도록 주의하세요. (Notion에서 token값을 얻어오는 방법과 페이지 주소를 얻어오는 방법은 구글 검색으로 확인해보세요.)
# 4. my_notion.py 파일을 코드가 저장된 곳과 같은 폴더에 넣어주세요.
# 5. 이 코드는 한겨레 아카이브 작업을 위해 만든 코드입니다. 그래서 한겨레신문사DB를 읽는 것에 특화되어 있습니다. 다른 언론사의 정보를 이용하시려면 함수 아래 각 변수들을 다르게 지정하셔야 합니다. 원하는 언론사 홈페이지에 들어가 URL을 읽고, 크롬개발자도구를 열어 selector를 확인해주셔야 합니다. (크롬개발자도구 사용에 대해서는 구글 검색을 권해드립니다.)

# 용어 :
# 1. 스크래핑 전용 페이지 : 긁어온 URL들을 Web Bookmark 형식으로 저장할 노션 페이지입니다. 스크래핑용으로 전영 페이지를 만들어놓고, 한번 스크래핑이 끝날 때마다 북마크들을 다른 페이지로 옮겨 비워두면, 코드를 바꾸지 않아도 되어 편리합니다. 
# 2. 목차페이지 : 검색 결과가 나타나는 페이지입니다. 한겨레 신문의 경우 한 페이지에 열다섯개씩 기사 주소가 올라오기 때문에, 여러 개의 페이지가 생성됩니다. 메인함수에서 목차페이지를 나타내는 문자열 변수는 URL이고, 목차페이지들을 모은 리스트 변수는 URLs입니다. 목차페이지의 예는 : http://m.hani.co.kr/arti/SEARCH/news/date/리원량/list1.html
# 3. 기사주소 : 하나의 목차페이지는 그 안에 열다섯개까지 기사주소를 보여줍니다. 메인함수에서 기사주소를 나타내는 문자열 변수는 url이고, 기사주소들을 모은 리스트 변수는 urls입니다. 기사주소의 예는 : http://m.hani.co.kr/arti/opinion/editorial/928585.html
# 4. 기사내용 : 기사주소를 타고 넘어가면 기사내용이 나옵니다. 이 프로그램의 목적은 기사주소만 노션의 스크래핑 전용페이지로 보내는 것이므로, 기사내용은 긁어오지 않습니다. 기사내용이 필요하실 경우, 기사내용을 문자열로 잘 긁어주는 라이브러리로 Newspaper3k를 추천드립니다. 잘 작동할 경우라면 BeautifulSoup보다 간편합니다. (Newspaper 역시 잘 되는 사이트와 잘 안되는 사이트가 있습니다. 한겨레 신문의 경우는 Newspaper로 기사내용이 잘 읽힙니다. 그러나 한겨레21의 기사내용은 잘 읽히지 않습니다.)

import my_notion
#my_notion.token은 내 notion의 token값
#my_notion.page는 내 notion의 page주소

# ---

# 다음 함수들은 한겨레신문사DB를 읽는 것에 특화되어 있습니다. 다른 언론사의 정보를 이용하려면 함수 아래 각 변수들을 다르게 설정해야 합니다. 언론사 홈페이지에 들어가 URL을 읽으며 하나하나 고치는 일은 어렵지는 않지만 조금 귀찮기는 할 것 같습니다.

def count_lists(keyword) :
    
    """
    목차페이지가 모두 몇 페이지가 있나 점검합니다.
    BeautifulSoup와 정규표현식으로 전체 기사목록의 수를 읽어 반환합니다.
    """

    media = "news" #변경 #한겨레21을 검색하려면 "magazine"
    
    url =  "http://m.hani.co.kr/arti/SEARCH/" + media + "/date/" + keyword + "/list.html"

    html = requests.get(url)
    soup = BeautifulSoup(html.text, "html.parser")
    
    selector = "body > div > main > section.search.top.shadow > span.count" #변경 #크롬개발자도구 이용
    
    count_str = str(soup.select(selector)[0])
    count = int(re.findall('\d+', count_str)[0])
    
    print("뉴스 {}건".format(count))
    return count


def generate_URL(keyword, last_page):
    media = "news" #변경 #한겨레21을 검색하려면 "magazine"

    """
    목차 페이지의 주소를 하나하나 생성합니다. 생성된 주소들을 모아 리스트로 반환합니다.
    """
    
    page = 0
    URLs = []
    
    for page in reversed(range(last_page)) : #옛날기사가 앞에 오도록

        page = page +1
        
        page_no = str(page)
        URL = "http://m.hani.co.kr/arti/SEARCH/" + media + "/date/" + keyword + "/list" + page_no + ".html"
        URLs.append(URL)
           
    return URLs


def get_urls(URL):
    html = requests.get(URL)
    soup = BeautifulSoup(html.text, "html.parser")
    
    """
    목차페이지를 하나하나 불러와 각각의 페이지에 들어 있는 기사주소를 뽑아 모아 리스트로 반환합니다.
    """
    
    selector_for_list = 'body > div > main > section.search.top.shadow > ul > li > article > div > h4 > a'  #변경 #크롬개발자도구 이용 
    list = soup.select(selector_for_list)
    
    urls = []
    for link in reversed(list):
        u = link.get('href') #변경 #크롬개발자도구 이용
        urls.append(u)
        
    return urls


def export(url):
    
    """
    기사주소를 Notion의 스크래핑 전용 페이지로 보내 WebBookmark를 생성해줍니다.
    """
    
    client = NotionClient(token_v2 = my_notion.token)
    page = client.get_block(my_notion.page)
    
    print("{}에 {}를 보내는 중...".format(page.title, url))

    try :
        newchild = page.children.add_new(BookmarkBlock, link=url)
        newchild.set_new_link(url)
    except : # Web Bookmark가 생성이 안될 경우 url만 표시해줍니다
        text = page.children.add_new(TextBlock)
        text.title = url


def main() :
    last_page = 0 #초기화
    keyword = str(input("키워드(또는 키워드+키워드) >>"))

    count = count_lists(keyword)
    last_page = math.ceil(count/15)
    
    URLs = generate_URL(keyword, last_page)

    whole_lists = []
    for URL in URLs :
        
        time.sleep(3) #신문사 서버에 무리를 주지 않기 위한 delay
           # 괄호 안의 숫자(초)를 바꾸어 지연 시간을 바꿀 수 있습니다.
           # 충분한 지연시간을 주어야 신문사 서버에 무리를 주지 않고
           # '서버 공격'으로 오인돼 차단당할 가능성을 줄일 수 있습니다.    

        urls = get_urls(URL)
        whole_lists.extend(urls)
  
    print("\n전체 기사수는 : " + str(len(whole_lists)) + "\n\n")
    print("\n전체 페이지는 : " + str(last_page) + "\n\n")
    
    print(whole_lists)
    
    for url in whole_lists :
        export(url)
        


# 1. main()함수를 실행시키면 "키워드"를 묻는 창이 나옵니다. 복수의 키워드를 넣을 때에는 "%20" 또는 "+" 기호를 넣어 공백없이 연결해주시면 됩니다. 
# 2. 키워드 입력 후 전체 검색수와 전체 페이지수를 보고 너무 적거나 많다 싶으면 중단시키고 처음부터 다시 실행하면 됩니다. 너무 많으면 실행 중 에러가 발생하기도 합니다. (제 작업환경에서는 100~200건 정도가 부담없이 잘 돌아갔습니다. 1천건은 제 컴에도 신문사 DB에도 별로 좋지 않을 것 같습니다. 사실 건수가 너무 많아지면 긁어온다한들 다 읽기도 힘들고 노션에도 한 페이지에 저장하는 의미가 없습니다.)
# 3. 신문사 서버에서 url을 긁어오는 시간이 오래 걸릴 수 있습니다. 서버에 부담을 주어 디도스 공격 따위로 오인 받지 않기 위해, 일부러 delay를 주기 때문입니다. 기다리기 불편하시면 time.sleep(초) 함수를 조정하시면 됩니다.
# 4. 에러로 작업이 중단되는 것을 피하기 위해 '예외 처리'를 코드에 넣었습니다. 이 경우 Web Bookmark가 생성되지 않고 URL만 텍스트로 찍힙니다(아마 잘못된 링크일 가능성이 큽니다.)
# 5. 그러나 서버나 인터넷의 문제 등 예상하지 못한 상황 때문에 에러가 발생할 수도 있습니다. 이때는 실행을 중단시키고 다시 실행하면 됩니다. 다만 이때, Notion 페이지에 먼저 생성된 주소 목록은 지워지지 않기 때문에 Notion 페이지를 한번 정리한 후 다시 실행시키면 됩니다.

if __name__ == "__main__":
    main()

# ---
