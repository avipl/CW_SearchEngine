import sys, lucene
import os, shutil
import pandas as pd
import time
import json

from java.lang import System
from java.nio.file import Path, Paths
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import \
    Document, Field, StoredField, StringField, TextField, FieldType
from org.apache.lucene.index import \
    IndexOptions, IndexWriter, IndexWriterConfig, DirectoryReader, \
    FieldInfos, MultiFields, MultiTerms, Term
from org.apache.lucene.util import PrintStreamInfoStream
from org.apache.lucene.queryparser.classic import \
    MultiFieldQueryParser, QueryParser
from org.apache.pylucene.queryparser.classic import PythonQueryParser
from org.apache.lucene.search import BooleanClause, IndexSearcher, TermQuery, MatchAllDocsQuery
from org.apache.lucene import search
from org.apache.lucene.store import MMapDirectory, NIOFSDirectory
from org.apache.lucene.util import BytesRefIterator
from org.apache.lucene.search.similarities import BM25Similarity
from org.apache.lucene.document import IntPoint, FloatPoint
import pdb

usage = """
    usage: python3 index_search.py [index | search] [search_query]
    where
        "index" => create index
        "search" => search the index for "search_query"
"""

def data_cleaning(file):
    df=pd.read_csv(file, na_filter=False, dtype={"year":"object", "rating":"object", "votes":"object", "runtime":"object"})

    print("-Reading file " + file + "...")
    print("-Droppping columns...")
    df.drop(["meta_score", "gross"], axis=1, inplace=True)
    df = df.drop_duplicates(subset='movie_id', keep="first")

    print("-Processing null values...")
    df['cast'] = df['cast'].str.replace('^$','Unknown', regex=True)
    df['director'] = df['director'].str.replace('^$','Unknown', regex=True)
    df['genre'] = df['genre'].str.replace('^$','Unknown', regex=True)
    df['plot'] = df['plot'].str.replace('^$','Unknown', regex=True)
    df['certificate'] = df['certificate'].str.replace('^$','Unknown', regex=True)

    df['year'] = df['year'].str.replace('^$','0', regex=True)
    df['rating'] = df['rating'].str.replace('^$','0', regex=True)
    df['runtime'] = df['runtime'].str.replace('^$','0', regex=True)
    df['runtime'] = df['runtime'].str.rstrip(' min')
    df['runtime'] = df['runtime'].str.replace(',','')
    df['votes'] = df['votes'].str.replace('^$','0', regex=True)
    df['votes'] = df['votes'].str.replace(',','')
    
    df = df.astype({"year": int, "runtime": int, "votes": int, "rating": float})
    
    df['all_fields'] = df[['movie_name', 'cast', 'director', 'genre', 'certificate', 'year']].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)

    return df

class CustomQueryParser(PythonQueryParser):
    def __init__(self, f, a):
        super(CustomQueryParser, self).__init__(f, a)
    
    def getFieldQuery_quoted(_self, field, queryText, quoted):
        query =  super(CustomQueryParser, _self).getFieldQuery_quoted_super(field, queryText, quoted)
        if "votes" == field or "runtime" == field or "year" == field:
            if queryText is not None: queryText = int(queryText)
            return IntPoint.newExactQuery(field, queryText)
        
        if "rating" == field:
            if queryText is not None: queryText = float(queryText)
            return FloatPoint.newExactQuery(field, queryText)
        
        return query
        
    def getRangeQuery(_self, field, part1, part2, lowerInclusive, upperInclusive):
        query = super(CustomQueryParser, _self).getRangeQuery(field, part1, part2, lowerInclusive, upperInclusive)
        if "votes" == field or "runtime" == field or "year" == field:
            if part1 is not None: part1 = int(part1)
            else: part1 = 0 #votes and runtime are non-negative integers
            if part2 is not None: part2 = int(part2)
            else: part2 = 2147483647 # INT32 max
            return IntPoint.newRangeQuery(field, part1, part2)
        
        if "rating" == field:
            if part1 is not None: part1 = float(part1)
            else: part1 = 0.0 #rating is non-negative float
            if part2 is not None: part2 = float(part2)
            else: part2 = 10.0 # max rating 10.0
            return FloatPoint.newRangeQuery(field, part1, part2)
        
        return query
        
            
def create_index(dir, df):
    if not os.path.exists(dir):
        os.mkdir(dir)

    store = NIOFSDirectory(Paths.get(dir))
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    writer = IndexWriter(store, config)

    storeType = FieldType() 
    storeType.setStored (True)
    storeType.setTokenized (True)
    storeType.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS_AND_OFFSETS)
    
    bodyType = FieldType()
    bodyType.setStored(False)
    bodyType.setTokenized(True)
    bodyType.setIndexOptions(IndexOptions.DOCS_AND_FREQS)
    
    idType = FieldType()
    idType.setStored(True)
    idType.setTokenized(False)
    idType.setIndexOptions(IndexOptions.NONE)

    df = df.reset_index()
    doc_cnt = len(df.index)
    
    for index, row in df.iterrows():
        #don't wanna tokenize
        year = row['year']
        rating = row['rating']
        votes = row['votes']
        runtime = row['runtime']
        
        # not useful for search 
        movie_id = row['movie_id']
        movie_url = row['movie_url']
        
        # wanna tokenize
        cast = row['cast']
        director = row['director']
        genre = row['genre']
        plot = row['plot']
        name = row['movie_name']
        cert = row['certificate']
        
        # all fields combined, want to index but don't want store the field
        all_fields = row['all_fields'] + " " +row['plot']
                    
        doc = Document()
        
        # Following fields contains number use float/int point for faster exact/range queries
        doc.add(StoredField('votes', votes)) 
        doc.add(IntPoint('votes', votes)) 
        doc.add(StoredField('runtime', runtime)) 
        doc.add(IntPoint('runtime', runtime)) 
        doc.add(StoredField('year', year)) 
        doc.add(IntPoint('year', year)) 
        
        doc.add(FloatPoint('rating', rating)) 
        doc.add(StoredField('rating', rating)) 
        
        doc.add(Field('movie_id', str(movie_id), idType))
        doc.add(Field('movie_url', str(movie_url), idType))
        
        doc.add(Field('cast', str(cast), storeType))
        doc.add(Field('director', str(director), storeType))
        doc.add(Field('genre', str(genre), storeType))
        doc.add(Field('plot', str(plot), storeType))
        doc.add(Field('name', str(name), storeType)) 
        doc.add(Field('certificate', str(cert), storeType))
        
        doc.add(Field('all_fields', str(all_fields), bodyType))
        
        writer.addDocument(doc)

    writer.close()
    return doc_cnt
    
if __name__ == '__main__':
    lucene.initVM()
    
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))      
    df = data_cleaning("./sample.csv")
    print("-Creating index...")
    start_time = time.time()
    num_doc = create_index("./../lucene_index", df)
    end_time = time.time();
    print("-" + str(num_doc) + " docs indexed in " + str(end_time - start_time) + "s")