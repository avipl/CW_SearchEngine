#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Now running LUCENE..."
    python3 index_search.py
    
    echo "Now running BERT..."
    python3 bert_final.py
    exit
fi

if [ $# -ne 1 ]; then
    echo "$0 [BERT|LUCENE] "
    exit
fi

TEST=$1

if [[ "$TEST" != "BERT" ]] && [[ "$TEST" != "LUCENE" ]]; then
     echo "$0 [BERT|LUCENE]"
     exit
fi

if [[ $TEST == "BERT" ]]; then
echo "Now running BERT..."
    python3 bert_final.py
else
 echo "Now running LUCENE..."
    python3 index_search.py
fi