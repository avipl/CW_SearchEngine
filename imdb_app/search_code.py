from . import bert, lucene

class Search():
    def __init__(self, search_query, search_type):
        self.query = search_query
        self.type =  search_type
    def res_return(self):
        if self.type=="bert":
            li=bert.bert_query(self.query)
            return li
        else:
            li=lucene.lucene_query(self.query)
            return li
            
    