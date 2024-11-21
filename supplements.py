import pandas as pd
from overlap import overlap

def preprocess_data():
    data = pd.read_csv("Sports Supplements.csv")

    # Custom aggregation functions
    def concatenate_strings(series):
        return '|'.join(series.dropna().unique())  # Remove duplicates and NaN

    def sum_values(series):
        return series.sum()

    def max_value(series):
        return series.max()

    def average(series):
        # Remove invalid entries (e.g., '-')
        valid_series = series[series != '-']

        if valid_series.empty:
            return None  # Return None or any placeholder for blank fields

        numeric_series = valid_series.str.rstrip('%').astype(float)
        return numeric_series.mean()

    def combine_claims_and_evidence(claims, evidence):
        # Pair each claim with its corresponding evidence level
        combined = []
        for claim, score in zip(claims, evidence):
            if pd.notna(claim) and pd.notna(score):  # Ensure both are valid
                combined.append((claim.strip(), score))
        return combined

    def unique_sorted_strings(series):
        return '|'.join(sorted(set(series.dropna())))

    # Apply pairing of claims and evidence
    data['Claim-Evidence'] = data.apply(
        lambda row: combine_claims_and_evidence(
            row['Claimed improved aspect of fitness'].split('|') if pd.notna(
                row['Claimed improved aspect of fitness']) else [],
            [row[
                 "evidence level - score. 0 = no evidence, 1,2 = slight, 3 = conflicting , 4 = promising, 5 = good, 6 = strong "]] * len(
                row['Claimed improved aspect of fitness'].split('|')) if pd.notna(
                row['Claimed improved aspect of fitness']) else []
        ),
        axis=1
    )

    # Drop the old "Claimed improved aspect of fitness" and evidence level columns
    data = data.drop(columns=[
        'Claimed improved aspect of fitness',
        "evidence level - score. 0 = no evidence, 1,2 = slight, 3 = conflicting , 4 = promising, 5 = good, 6 = strong "
    ])

    # Custom aggregation functions for new combined claims-evidence column
    def aggregate_claim_evidence(series):
        combined = []
        for item in series.dropna():
            combined.extend(item)  # Flatten the lists of tuples
        return combined

    # Define the aggregation rules
    aggregation_rules = {
        'alt name': concatenate_strings,
        'Claim-Evidence': aggregate_claim_evidence,
        "fitness category": concatenate_strings,
        "sport or exercise type tested": concatenate_strings,
        "popularity": average,
        "number of studies examined": sum_values,
        "number of citations": max_value,
        "efficacy": concatenate_strings,
        "notes": concatenate_strings,
        "% positive studies/ trials": average
        # Add other columns and aggregation functions as needed
    }

    # Group by 'supplement' and apply the aggregation rules
    condensed_data = data.groupby('supplement').agg(aggregation_rules).reset_index()

    # Save to CSV
    condensed_data.to_csv("Condensed_Sports_Supplements.csv", index=False)
    #print("Condensed dataset has been written to 'Condensed_Sports_Supplements.csv'.")

    return condensed_data


import ast

def load_claims(data):
    supplement_claims = {}
    for _, row in data.iterrows():
        try:
            # Safely evaluate the Claim-Evidence string to a Python list
            claim_evidence_list = ast.literal_eval(row['Claim-Evidence'])
            supplement_claims[row['supplement']] = claim_evidence_list
        except (ValueError, SyntaxError):
            # If parsing fails, skip or assign an empty list
            supplement_claims[row['supplement']] = []
    return supplement_claims

def supplement_recommendation(data, claims, prompt):
    text = prompt.lower().split('supplement')[1].strip()
    #print(text)

    supplement_names = data['supplement'].tolist()
    supplement_names = set(supplement_names)

    ranking = {name: 0 for name in supplement_names}

    # add points based on overlap.
    for name, the_claims in claims.items():
        overlap_score = 0
        for claim_evidence in the_claims:
            claim = claim_evidence[0]
            evidence = claim_evidence[1]
            claim_overlap = overlap(text, claim)
            overlap_score += (claim_overlap * evidence/2) * 0.75
        ranking[name] += overlap_score

    # add points based on % of good studies
    for name in supplement_names:
        percent_good = data.loc[data['supplement'] == name, "% positive studies/ trials"].iloc[0]
        num_of_studies = data.loc[data['supplement'] == name, "number of studies examined"].iloc[0]
        popularity = data.loc[data['supplement'] == name, "popularity"].iloc[0]
        ranking[name] += (popularity/24100) * 0.1
        if percent_good > 0:
            ranking[name] += (percent_good/100) * (1.00*(num_of_studies/56))

    # add score for notes, weighted less heavily than the claims.
    for name in supplement_names:
        notes_overlap_score = 0
        sport_overlap_score = 0
        notes = data.loc[data['supplement'] == name, "notes"].iloc[0]
        sport = data.loc[data['supplement'] == name, "sport or exercise type tested"].iloc[0]
        # Ensure notes is a string or set to empty if NaN
        if pd.isna(notes):
            notes = ""
        elif not isinstance(notes, str):
            notes = str(notes)

        sport_overlap_score += overlap(text, sport) * 0.2
        notes_overlap_score += (overlap(text, notes) * 0.2)
        ranking[name] += notes_overlap_score
        ranking[name] += sport_overlap_score


    # Sort the ranking with tie-breaking
    sorted_ranking = list(sorted(
        ranking.items(),
        key=lambda item: (
            item[1],  # Primary sort: score
            data.loc[data['supplement'] == item[0], "number of studies examined"].iloc[0] if not data.loc[
                data['supplement'] == item[0], "number of studies examined"].empty else 0
        ),
        reverse=True
    ))
    print(sorted_ranking)

    supp1 = sorted_ranking[0][0]
    supp2 = sorted_ranking[1][0]
    supp3 = sorted_ranking[2][0]

    top_supplements = [supp1, supp2, supp3]
    if "Whey protein" in top_supplements and "Soy protein" in top_supplements:
        # Find the lower-ranked protein and replace it with the next-ranked supplement
        whey_rank = top_supplements.index("Whey protein")
        soy_rank = top_supplements.index("Soy protein")

        # Determine the lower-ranked protein
        lower_ranked_index = max(whey_rank, soy_rank)
        next_supplement = sorted_ranking[3][0]  # Pick the next-ranked supplement (4th in the list)

        # Replace the lower-ranked protein
        top_supplements[lower_ranked_index] = next_supplement

    # Unpack the top 3 supplements
    supp1, supp2, supp3 = top_supplements

    recommendation_headline = f"I would recommend {supp1}, {supp2} and {supp3}. "

    evidence_threshold = 0
    supp1_detail = (', '.join([statement[0] for statement in claims[supp1] if statement[1] > 1])) if any(statement[1] >= evidence_threshold for statement in claims[supp1]) else 'No proven benefits'
    supp2_detail = (', '.join([statement[0] for statement in claims[supp2] if statement[1] > 1])) if any(statement[1] >= evidence_threshold for statement in claims[supp2]) else 'No proven benefits'
    supp3_detail = (', '.join([statement[0] for statement in claims[supp3] if statement[1] > 1])) if any(statement[1] >= evidence_threshold for statement in claims[supp3]) else 'No proven benefits'

    if supp1_detail == "" or supp1_detail is None: supp1_detail = ""
    else: supp1_detail = f"{supp1} {('helps with ' + supp1_detail)}. "

    if supp2_detail == "" or supp2_detail is None: supp2_detail = ""
    else: supp2_detail = f"{supp2} {('aids with ' + supp2_detail)}. "

    if supp3_detail == "" or supp3_detail is None: supp3_detail = ""
    else: supp3_detail = f"{supp3} {('is useful for ' + supp3_detail)}. "

    detail = (
        f"{supp1_detail}"
        f"{supp2_detail}"
        f"{supp3_detail}"
    )
    print(recommendation_headline)
    print(detail)
    response = f"{recommendation_headline}{detail}"
    return response