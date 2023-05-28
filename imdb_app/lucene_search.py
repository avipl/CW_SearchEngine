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
from org.apache.lucene.search import BooleanClause, IndexSearcher, TermQuery
from org.apache.lucene.store import MMapDirectory, NIOFSDirectory
from org.apache.lucene.util import BytesRefIterator
from org.apache.lucene.search.similarities import BM25Similarity
from org.apache.lucene.document import IntPoint, FloatPoint

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


def lucene_query(query, k=5):
    lucene.getVMEnv().attachCurrentThread()
    indexDir = NIOFSDirectory(Paths.get('/home/avipl1994/CW_SearchEngine/imdb_app/lucene_index'))
    searcher = IndexSearcher(DirectoryReader.open(indexDir))
    
    parser = CustomQueryParser('all_fields', StandardAnalyzer())
    parsed_query = parser.parse(query)
    
    topDocs = searcher.search(parsed_query, k).scoreDocs
    topkdocs = []
    for hit in topDocs:
        doc = searcher.doc(hit.doc)
        topkdocs.append({
            "score": hit.score,
            "name": doc.get("name"),
            "year": doc.get("year"),
            "rating": doc.get("rating"),
            "votes": doc.get("votes"),
            "runtime": doc.get("runtime"),
            "certificate": doc.get("certificate"),
            "cast": doc.get("cast"),
            "director": doc.get("director"),
            "genre": doc.get("genre"),
            "plot": doc.get("plot"),
            "movie_id": doc.get("movie_id"),
            "movie_url": doc.get("movie_url")
        })
        
    return json.dumps(topkdocs)