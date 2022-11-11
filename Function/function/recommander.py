import numpy as np
import pandas as pd

import dill

from collections import defaultdict

#Loading the data files
with open('function/Data/users.pkl','rb') as file:
	users = dill.load(file)
with open('function/Data/cosine_similarities.pkl','rb') as file:
	cosine_similarities = dill.load(file)
with open('function/Data/predictions.pkl','rb') as file:
	pred = dill.load(file)
with open('function/Data/article_ref.pkl','rb') as file:
	article_ref = dill.load(file)
with open('function/Data/articles_categ.pkl','rb') as file:
    articles_categ = dill.load(file)



def get_top_n(predictions, n=10):
    # First we map the predictions to each user.
    top_n = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        top_n[uid].append((iid, est))

    # Then we sort the predictions for each user and retrieve the k highest ones.
    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]

    return top_n


def findRecom(dic, userId):
    res = []
    query = dic[userId]
    for uid, user_ratings in query:
        res.append(uid)
    return res

def compute_sim_score(article_id):
    sim_scores = list(enumerate(cosine_similarities[article_id]))

    return sim_scores

def hyb_article_rec(user_id: int):
    subset = users.loc[users.user_id == user_id]

    article_similarity_score = []
    #Computing the similarity scores of each articles browsed by the users
    for index, row in subset.iterrows():
        #Finding the index of the articles in the cosine similarities matrix
        article_index = article_ref.loc[article_ref.article_id==row['click_article_id']].index.values[0]
        #Adding the compute_sim_score x times, with x being the number of user clicks on the article
        article_similarity_score += row['clicks']*compute_sim_score(article_index)
    
    #Gathering results in a dataframe    
    rec = pd.DataFrame(article_similarity_score,
                       columns=['article_id','sim_score']).set_index('article_id')
    
    #Removing negative similarities to prevent penalization of uncorrelated articles, and aggregating by article_id
    rec = rec.loc[rec.sim_score > 0].groupby('article_id').sum()
    
    #Removing articles already read by the user from dataframe
    rec = rec.loc[~rec.index.isin(subset.click_article_id.unique())]
    
    #Merging our recommendations with article categories
    rec = rec.merge(articles_categ, on='article_id', how='inner')
    
    #Finding 5 categories recommendations for our top user
    categ_recom = findRecom(get_top_n(pred, n=5),5463)
    
    #If we get valid category predictions
    if len(categ_recom) > 0:
        cat = []
        #Compute the score for each one with our custom scoring function
        for i in range(len(categ_recom)):
            cat.append({'category_id' :categ_recom[i], 'score':((8-i)/2)})

        cat = pd.DataFrame(cat)
        
        #Merging our category scores with our recommendations, giving a score of 1 to articles not belonging to the top5 categ
        final = rec.merge(cat, on='category_id', how='left').fillna(1)
        
        #Calculating our final score by multiplying the similarity score and the category score
        final['final_score'] = final['score']*final['sim_score']
        
        #Returning top 5 matches
        return final.sort_values(by='final_score', ascending=False).head(5).article_id.to_list()

    else:
        #Returning top 5 matches based solely on embeddings
        return rec.sort_values(by='sim_score', ascending=False).head(5).article_id.to_list()
