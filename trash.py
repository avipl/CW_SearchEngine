data=[{'score': '39.480453', 'name': 'The Menu', 'year': '2023.0', 'rating': '', 'votes': '', 'runtime': '', 'certificate': '', 'cast': 'James Tratas,Carlotta Morelli,Jack McCallum', 'director': 'Natasha Kinaru', 'genre': 'Short,Comedy,Drama', 'plot': 'Director:', 'movie_id': 'tt2373990'}, {'score': '39.480453', 'name': 'Olla', 'year': '2019.0', 'rating': '6.8', 'votes': '1896.0', 'runtime': '27 min', 'certificate': '', 'cast': 'Romanna Lobach,Gregoire Tachnakian,Jenny Bellay,Gall Gaspard', 'director': 'Ariane Labed', 'genre': 'Short,Comedy,Drama', 'plot': "OLLA answers an ad on a dating website for Eastern European women. Shortly thereafter, she moves in with Pierre who lives with his elderly mother and things don't go as expected.", 'movie_id': 'tt1038420'}, {'score': '39.480453', 'name': 'Stud Boob', 'year': '2020.0', 'rating': '', 'votes': '', 'runtime': '', 'certificate': '', 'cast': 'Ashley Williams,Kimberly Williams-Paisley', 'director': 'Shaina Feinberg', 'genre': 'Short,Drama', 'plot': 'Two sisters in a bathroom debate their different approaches to the patriarchy.', 'movie_id': 'tt9387220'}, {'score': '39.480453', 'name': 'Boobs in Arms', 'year': '1940.0', 'rating': '7.8', 'votes': '557.0', 'runtime': '18 min', 'certificate': 'Approved', 'cast': 'Moe Howard,Larry Fine,Curly Howard,Richard Fiske', 'director': 'Jules White', 'genre': 'Short,Comedy,War', 'plot': 'The stooges are greeting card salesmen who are mistakenly inducted into the army after escaping from the jealous husband of one of their customers. In bootcamp their sergeant turns out to ...', 'movie_id': 'tt0032270'}, {'score': '39.480453', 'name': 'Vacation Sex', 'year': '2012.0', 'rating': '6.7', 'votes': '69.0', 'runtime': '4 min', 'certificate': 'TV-MA', 'cast': 'Lizzy Caplan,Kathryn Hahn,Jake Johnson,Rob Riggle', 'director': 'Lauryn Kahn', 'genre': 'Short,Comedy', 'plot': "What happens in your bed when you're on vacation?", 'movie_id': 'tt2221914'}]

data[0]["movie_id"]='tt17663992'
data[1]["movie_id"]='tt11145118'
data[2]["movie_id"]='tt6710474'
data[3]["movie_id"]='tt14209916'
data[4]["movie_id"]='tt13833688'

import requests
from bs4 import BeautifulSoup
movie_urls=[]
for i in data:
    movie_urls.append("https://imdb.com/title/"+i["movie_id"])

headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}
ct=0
for i in movie_urls:
    response=requests.get(i,headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    ilink=soup.find("a", {"class": "ipc-lockup-overlay ipc-focusable"})
    n_url="https://www.imdb.com/"+ilink['href']
    n_response=requests.get(n_url,headers=headers)
    n_soup=BeautifulSoup(n_response.text, 'html.parser')
    iid=n_url.split("/")[-2]+"-curr"
    img=n_soup.find("img",{"data-image-id":iid})
    data[ct]["image_url"]=img["src"]
    ct+=1
    print(img["src"])