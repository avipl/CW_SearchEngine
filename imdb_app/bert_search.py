from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
import faiss                   # make faiss available
import pandas as pd
import os, shutil
import sys
import json
import math
import sqlite3

def convert_to_embedding(query):
    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-distilroberta-v1') # you can change the model here
    model = AutoModel.from_pretrained('sentence-transformers/all-distilroberta-v1')
    
    tokens = {'input_ids': [], 'attention_mask': []}
    new_tokens = tokenizer.encode_plus(query, max_length=512,
                                       truncation=True, padding='max_length',
                                       return_tensors='pt')
    tokens['input_ids'].append(new_tokens['input_ids'][0])
    tokens['attention_mask'].append(new_tokens['attention_mask'][0])
    tokens['input_ids'] = torch.stack(tokens['input_ids'])
    tokens['attention_mask'] = torch.stack(tokens['attention_mask'])
    with torch.no_grad():
        outputs = model(**tokens)
    embeddings = outputs.last_hidden_state
    attention_mask = tokens['attention_mask']
    mask = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
    masked_embeddings = embeddings * mask
    summed = torch.sum(masked_embeddings, 1)
    summed_mask = torch.clamp(mask.sum(1), min=1e-9)
    mean_pooled = summed / summed_mask
    
    return mean_pooled[0] # assuming query is a single sentence

def bert_query(query, k = 5):
    query_embedding = convert_to_embedding(query)
    index_loaded = faiss.read_index("/home/cs242/lucene_test/IR_Project/imdb_app/bert_index.index")
    scores, indices = index_loaded.search(query_embedding[None, :], k)
    conn = sqlite3.connect('/home/cs242/lucene_test/IR_Project/imdb_app/mydb.sqlite')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    topkdocs = []
    cnt = 0
    for i in indices[0]:
        if i >= 0:
            cur.execute('SELECT * FROM movie_data WHERE "index" = :id', {"id": str(i)})
            row = cur.fetchone()
            topkdocs.append({
                "score": str(scores[0][cnt]),
                "name": row["movie_name"],
                "year": str(row["year"]),
                "rating": str(row["rating"]),
                "votes": str(row["votes"]),
                "runtime": str(row["runtime"]),
                "certificate": row["certificate"],
                "cast": row["cast"],
                "director": row["director"],
                "genre": row["genre"],
                "plot": row["plot"],
                "movie_id": row["movie_id"]
            })
        cnt = cnt + 1 
    return json.dumps(topkdocs)