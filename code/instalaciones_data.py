import streamlit as st
import requests
import pandas as pd

API_KEY = '4e1f86110caa98dbcd444fdf6229e002'
FORM_ID = '250216539146152'

def get_field_map():
    url = f'https://api.jotform.com/form/{FORM_ID}/questions?apiKey={API_KEY}'
    response = requests.get(url)
    questions = response.json()['content']
    return {str(qid): qdata['text'] for qid, qdata in questions.items()}

def fetch_jotform_json():
    all_submissions = []
    offset = 0
    while True:
        url = f'https://api.jotform.com/form/{FORM_ID}/submissions?apiKey={API_KEY}&limit=1000&offset={offset}'
        data = requests.get(url).json()
        batch = data['content']
        if not batch:
            break
        all_submissions.extend(batch)
        offset += 1000
    return all_submissions

def clean_jotform_data(submissions, field_map):
    flat_list = []
    for submission in submissions:
        flat = {}
        for k, v in submission['answers'].items():
            label = field_map.get(k, k)
            ans = v.get('answer', None)
            if isinstance(ans, dict):
                for subk, subv in ans.items():
                    flat[f"{label}_{subk}"] = subv
            else:
                flat[label] = ans
        flat_list.append(flat)
    df = pd.DataFrame(flat_list)
    # --- Add your custom cleaning here ---
    # For example: rename columns, parse dates, drop empty columns, etc.
    return df

st.title("Jotform Submissions (Cleaned Table)")

if st.button("Refresh Data"):
    with st.spinner("Fetching and cleaning latest submissions..."):
        field_map = get_field_map()
        submissions = fetch_jotform_json()
        df = clean_jotform_data(submissions, field_map)
        st.success(f"Fetched and cleaned {len(df)} submissions!")
        st.dataframe(df)

# Fetch and display the first 5 rows
field_map = get_field_map()
submissions = fetch_jotform_json()
df = clean_jotform_data(submissions, field_map)
print(df.head(5))  