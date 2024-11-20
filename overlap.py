import re
import nltk

match = 0
match_list = []

def tokenize(text):
    return nltk.word_tokenize(text.lower())

def get_ngrams(words, n):
    return [(i, words[i:i + n]) for i in range(len(words) - n + 1)]

def overlap(text1, text2):
    #print("-----------New Gloss Set-----------")
    global match
    global match_list
    words1 = tokenize(text1)
    words2 = tokenize(text2)
    words1 = [word for word in words1 if not bool(re.fullmatch(r'\W+', word))]
    words2 = [word for word in words2 if not bool(re.fullmatch(r'\W+', word))]

    matched_indices_1 = set()  # To store indices of words in gloss1 that are already matched
    matched_indices_2 = set()  # To store indices of words in gloss2 that are already matched
    overlap_score = 0

    # Try to match n-grams from largest to smallest
    for n in range(min(len(words1), len(words2)), 0, -1):

        #print(f"checking n-grams of size {n}")
        ngrams1 = get_ngrams(words1, n)
        ngrams2 = get_ngrams(words2, n)

        # for each n-gram in gloss1, check if it matches an n-gram in gloss2
        for i, ngram1 in ngrams1:
            if any(x in matched_indices_1 for x in range(i, i + n)):
                continue  # Skip if any part of this n-gram is already matched

            for j, ngram2 in ngrams2:
                if any(x in matched_indices_2 for x in range(j, j + n)):
                    continue  # Skip if any part of this n-gram is already matched

                if ngram1 == ngram2:
                    overlap_score += n ** 1.5  # n-gram phrase contributes n^2 to the score
                    # overlap_score += n
                    # the indices as matched so they can't be used again
                    matched_indices_1.update(range(i, i + n))
                    matched_indices_2.update(range(j, j + n))
                    #print("MATCH:", ngram1)
                    match += 1
                    match_list.append(ngram1)
                    # print("match list", match_list)
                    # print("\t\t\t", words1)
                    # print("\t\t\t", words2)
                    break  # Move on to the next n-gram in gloss1

    return overlap_score
