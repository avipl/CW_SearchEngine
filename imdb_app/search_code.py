from . import bert_search, lucene_search
import requests
from bs4 import BeautifulSoup
import ast

class Search():
    def __init__(self, search_query, search_type, top_k):
        self.query = search_query
        self.type =  search_type
        self.top_k = top_k

    def res_return(self):
        if self.type=="bert":
            res_json=ast.literal_eval(bert_search.bert_query(self.query, self.top_k))
            return res_json
        else:
            res_json=ast.literal_eval(lucene_search.lucene_query(self.query, self.top_k))
            return res_json