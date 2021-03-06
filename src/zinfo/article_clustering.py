import pandas as pd
import numpy as np

# cluster algorithms
from sklearn.cluster import DBSCAN

# nlp modules
import spacy

nlp = spacy.load('en_core_web_lg')
MIN_ARTICLES = 10


# removes stop words and punctuation from title for vectorization
def preprocess_text(text):
    doc = nlp(text)
    tokens = [w.lower_ for w in doc if not (w.is_stop or w.is_punct)]
    preproc_text = " ".join(tokens)
    return preproc_text


def get_vectorized_titles(df):
    sent_vecs = {}
    # make each article title into a vector
    # TODO check to make sure that this try catch doesn't effect indexing
    for title in df.title:
        try:
            doc = nlp(preprocess_text(title))
            sent_vecs.update({title: doc.vector})
        except Exception as e:
            print(e)

    vectors = list(sent_vecs.values())
    titles = list(sent_vecs.keys())

    return vectors, titles


# gets a number of clusters to shoot for based on distribution of data
def get_target_cluster_num(trending_news):
    topics = trending_news.topic.value_counts()
    no_info = topics.loc[topics < MIN_ARTICLES].index
    num_important_topics = topics.drop(no_info).nunique()
    return num_important_topics


# TODO maybe make the step size smaller
def get_num_clusters_per_val(vectors, min_samples, start, end, step, decimal):
    num_clusters = []
    for i in [float(j) / decimal for j in range(start, end, step)]:
        dbscan = DBSCAN(eps=i, min_samples=min_samples, metric='cosine').fit(vectors)
        # gets number of non -1 clusters
        labels = dbscan.labels_
        unique_vals = np.unique(labels)
        unique_vals = unique_vals[1:]
        num_clusters.append(len(unique_vals))

    return num_clusters


# finds optimal epsilon value for dbscan clustering
# going off of the assumption that there should be about as many clusters as there are topics
def get_best_eps_val(vectors, target_cluster_num, min_samples, start=2, end=50, step=2, decimal=100):
    num_clusters = get_num_clusters_per_val(vectors, min_samples, start, end, step, decimal)

    difference_array = np.absolute(np.array(num_clusters) - target_cluster_num)
    index = difference_array.argmin()

    best_eps_val = (start / decimal) + ((step / decimal) * index)
    return best_eps_val


def get_best_min_sample_val(num_total_articles, factor=200):
    absolue_min = 2
    if num_total_articles <= absolue_min * factor:
        return absolue_min
    else:
        return int(num_total_articles / factor)


def cluster_articles(df):
    print("clustering articles...")

    vectors, titles = get_vectorized_titles(df)
    x = np.array(vectors)

    # finds best hyper parameters for dbscan
    min_articles = get_best_min_sample_val(len(df))
    target_cluster_num = get_target_cluster_num(df)
    eps = get_best_eps_val(x, target_cluster_num, min_articles)
    print("eps_val: " + str(eps) + "\n" + "min_samples: " + str(min_articles) + " \ntarget cluster num: " + str(
        target_cluster_num))

    # clusters articles using dbscan
    dbscan = DBSCAN(eps=eps, min_samples=min_articles, metric='cosine').fit(x)

    return pd.DataFrame({'label': dbscan.labels_, 'title': titles, 'vectors': vectors})
