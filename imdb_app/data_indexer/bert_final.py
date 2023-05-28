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
import time

def create_bert_index(dir, sentences, index):
    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-distilroberta-v1') # you can change the model here
    model = AutoModel.from_pretrained('sentence-transformers/all-distilroberta-v1')

    # initialize dictionary to store tokenized sentences
    tokens = {'input_ids': [], 'attention_mask': []}

    for sentence in sentences:
        # encode each sentence and append to dictionary
        new_tokens = tokenizer.encode_plus(sentence, max_length=512,
                                           truncation=True, padding='max_length',
                                           return_tensors='pt')
        tokens['input_ids'].append(new_tokens['input_ids'][0])
        tokens['attention_mask'].append(new_tokens['attention_mask'][0])

    # reformat list of tensors into single tensor
    tokens['input_ids'] = torch.stack(tokens['input_ids'])
    tokens['attention_mask'] = torch.stack(tokens['attention_mask'])
    
    with torch.no_grad():
        outputs = model(**tokens)
    
    embeddings = outputs.last_hidden_state
    
    # resize our attention_mask tensor:
    attention_mask = tokens['attention_mask']
    mask = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
    masked_embeddings = embeddings * mask
    
    # Then we sum the remained of the embeddings along axis 1, because we want to reduce the 512 tokens to 1 dimension
    summed = torch.sum(masked_embeddings, 1)
    
    # clamp returns the same tensor with a range given, clamp is used to replace the zeros to a very minimal value
    # to avoid divide by zero error
    summed_mask = torch.clamp(mask.sum(1), min=1e-9)
    mean_pooled = summed / summed_mask
    
    index.add(mean_pooled)
    faiss.write_index(index,"./../bert_index.index")

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

def search_index(query):
    query_embedding = convert_to_embedding(query)
    index_loaded = faiss.read_index("./bert_test.index")
    D, I = index_loaded.search(query_embedding[None, :], 5)
    return D, I;

def concat_values_noNaFilter(df):
    snippet = [] 
    for i in df.index:
        ans=""
        if 'Short' in df.iloc[i]['genre']:
            ans = ans + "The short film is titled " + df.iloc[i]['movie_name'] + "."
        else:
            ans = ans + "The film is titled " + df.iloc[i]['movie_name'] + "."

        if df.iloc[i]['cast']!='':
            ans = ans + "It stars " + df.iloc[i]['cast'] + "."

        if df.iloc[i]['director']!='':
            ans = ans + "It was directed by " + df.iloc[i]['director'] + "."

        if df.iloc[i]['genre']!='':
            genre_to_add = df.iloc[i]['genre'].replace(',Short','')
            genre_to_add = genre_to_add.replace('Short,','')
            genre_to_add = genre_to_add.replace('Short','')


            ans = ans + "It is of the genre(s) " + genre_to_add + "."

        if df.iloc[i]['year']!='':
            ans = ans + "It was released on " + str(int(float(df.iloc[i]['year']))) + "."

        if df.iloc[i]['plot']!='':
            ans = ans + "A short description is as follows: " + df.iloc[i]['plot']

        snippet.append(ans)
    
    return snippet
    
if __name__ == '__main__':
    df = pd.read_csv('./sample.csv', na_filter=False)
    df = df.drop_duplicates()
    
    sentences = concat_values_noNaFilter(df)
    del df
    index = faiss.IndexFlatIP(768)
    print("Creating index...")
    start_time = time.time()
    steps = 10
    for row_cnt in range(0, len(sentences), steps):
        print(str(row_cnt) + "/" + str(len(sentences)))
        create_bert_index(dir, sentences[row_cnt:row_cnt+steps], index)
    print("Index creation complete...")
    
    end_time = time.time();
    print("-" + str(len(sentences)) + " docs indexed in " + str(end_time - start_time) + "s")

    #Re-load the data into memory
    df = pd.read_csv('./sample.csv', na_filter=False)
    df = df.drop_duplicates()
    
    #Load data in sqllite
    print("-Creating database...")
    table_name = 'movie_data'
    conn = sqlite3.connect('../mydb.sqlite')
    sql_query = f'Create table if not Exists {table_name} (cast text, cast_id text, cast_url text, certificate text, director text, director_id text, director_url text, genre text, gross text, meta_score text, movie_id text, movie_name text, movie_url text, plot text, rating text, runtime text, votes text, year text)'
    conn.execute(sql_query)
    df.to_sql(table_name, conn, if_exists='replace', index=True)
    conn.commit()
    conn.close()
    print("-Database created")
