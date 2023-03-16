from . import bert, lucene

class Search():
    def __init__(self, search_query, search_type):
        self.query = search_query
        self.type =  search_type
    def res_return(self):
        if self.type=="bert":
            res_json=bert.bert_query(self.query)
            return res_json
        else:
            res_json=lucene.lucene_query(self.query)
            return res_json
            
    
