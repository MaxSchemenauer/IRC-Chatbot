import pandas as pd
import difflib
import nltk
import re

def overlap(first, second):
    desc1 = nltk.tokenize.word_tokenize(first)
    desc1 = [[re.sub(r'[^\w\s]', '', word), False] for word in desc1]
    desc1 = [i for i in desc1 if len(i[0]) > 0]
    desc2 = nltk.tokenize.word_tokenize(second)
    desc2 = [[re.sub(r'[^\w\s]', '', word), False] for word in desc2]
    desc2 = [i for i in desc2 if len(i[0]) > 0]
    n = min(len(desc1), len(desc2))
    score = 0
    while n > 0:
        score += check(desc1, desc2, n) * (n ** 2)
        n -= 1
    return score

def check(desc1, desc2, n):
    matches = 0
    for i1 in range(0, len(desc1) - n + 1):
        for i2 in range(0, len(desc2) - n + 1):
            d1 = desc1[i1:i1 + n]
            d2 = desc2[i2:i2 + n]
            flag = True
            if i1 + n <= len(desc1) and i2 + n <= len(desc2):
                for counter in range(n):
                    if d1[counter][0] != d2[counter][0] or d1[counter][1] == True or d2[counter][1] == True:
                        flag = False
                if flag:
                    for c in range(n):
                        d1[c][1] = True
                        d2[c][1] = True
                    matches += 1
    return matches

def has_target_genre(genres, target_genres):
    if not genres:  # Handle empty or NaN cases
        return False
    return any(genre in target_genres for genre in genres)

def secondary(df, target_genres):
    second = []
    for index, row in df.iterrows():
        matches = 0
        total = 0
        if row['genres'] != '[]':
            gen = row['genres'][1:-1].split("}, {")
            for g in gen:
                total += 1
                if g in target_genres:
                    matches += 1

            if matches / total > 0.99:
                second.append({'title': row['title'], 'overview': row['overview']})
    return pd.DataFrame(second)

def similarity(movie, df):
    target_genres = movie['genres'].iloc[0]
    primary_matches = df[df['genres'] == target_genres]
    desc = movie['overview'].iloc[0]
    titles = primary_matches['title'].tolist()[:100]
    descriptions = primary_matches['overview'].tolist()[:100]
    scores = []
    for d in descriptions:
        if type(d) == type(""):
            scores.append(overlap(desc, d))
        else:
            scores.append(-1)

    if len(scores) < 5:
        secondary_matches = secondary(df, target_genres)
        titles = secondary_matches['title'].tolist()
        print(f"secondary: {len(secondary_matches)}   total: {len(df)}")
        descriptions = secondary_matches['overview'].tolist()[:100]
        for d in descriptions:
            if type(d) == type(""):
                scores.append(overlap(desc, d))
            else:
                scores.append(-1)
    top6 = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:6]
    retlst = []
    for item in top6:
        retlst.append(titles[item])
    return retlst

def recommend(title):
    # Find book (normalize title) or respond saying the book isn't found
    # Find similarity scores for other books (in the same category)
    # Rank books and return top results
    recommendations = []
    df = pd.read_csv('movies_metadata.csv')
    df['budget'] = pd.to_numeric(df['budget'], errors='coerce')
    df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce')
    df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce')
    df = df[df['budget'] > 1000000]
    df = df[df['revenue'] > 1000000]
    df = df[df['vote_average'] > 5]
    df = df[['belongs_to_collection', 'genres', 'title', 'overview', 'production_companies', 'release_date', 'runtime']]
    df['title'] = df['title'].fillna('')
    closest_match = difflib.get_close_matches(title, df['title'], n=1, cutoff=0.0)
    if len(closest_match) == 0:
        return "Unknown movie"
    closest_match = closest_match[0]
    movie = df[df['title'] == closest_match].head(1)
    if pd.notna(movie['belongs_to_collection'].iloc[0]):
        collection = df[df['belongs_to_collection'] == movie['belongs_to_collection'].iloc[0]]
        recommendations = collection['title'].tolist()
        recommendations.remove(closest_match)

    if len(recommendations) < 5:
        similar = similarity(movie, df)

    j = 0
    print(recommendations, 5 - len(recommendations))
    flag = False
    for i in range(5 - len(recommendations)):
        if j < len(similar):
            print(closest_match)
            while similar[j] in recommendations or similar[j] == closest_match:
                j += 1
                if j >= len(similar):
                    flag = True
                    break
            if flag:
                break
            recommendations.append(similar[j])

    retstr = f"Movies similar to {closest_match} include:"
    i = 1
    for item in recommendations:
        if i == 1:
            retstr += f" {item}"
            i += 1
        else:
            retstr += f", {item}"
    return retstr

#recommend("Top Gun")
#print(recommend("star wars"))
#print(recommend("mad max fury road"))

