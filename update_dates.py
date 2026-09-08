import os
import glob
import re

def update_dates_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Add format="DD/MM/YYYY" to st.date_input
    # Find all st.date_input(..., format="DD/MM/YYYY") and insert format="DD/MM/YYYY" before the closing parenthesis
    # We match up to the last closing parenthesis of st.date_input
    def replacer(match):
        inner = match.group(1)
        if 'format=' in inner:
            return match.group(0) # already has format
        return f'st.date_input({inner}, format="DD/MM/YYYY")'

    content = re.sub(r'st\.date_input\(([^)]+)\)', replacer, content)

    # Now let's try to find common date columns in dataframes and add formatting.
    # It's safer to let Streamlit's global config or Pandas handle it, but Streamlit has st.dataframe formatting.
    # Since we can't reliably parse all pandas logic, we'll format known date columns we've seen.
    # Actually, we can add a block in app.py or in the files directly.
    # Let's focus on the date_input first.

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")

for py_file in glob.glob('C:/Users/MARCIO/Gestao_Fabrica_Alho/**/*.py', recursive=True):
    update_dates_in_file(py_file)
