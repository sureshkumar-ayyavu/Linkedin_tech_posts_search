import io
import re
from datetime import datetime, timezone
from urllib.parse import urlencode, urlparse
import xml.etree.ElementTree as ET

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

st.set_page_config(page_title='LinkedIn Technical Post Collector', page_icon='🔎', layout='wide')
st.title('🔎 LinkedIn Technical Post Collector')
st.caption('Discover publicly indexed LinkedIn posts via Bing RSS search. No LinkedIn login or scraping of restricted pages.')

DEFAULT = 'UCIe 2.0\nPCIe Gen6\nSignal Integrity\nSerDes equalization\nAdvanced Packaging'

def clean_html(value):
    return BeautifulSoup(value or '', 'html.parser').get_text(' ', strip=True)

def is_post(url):
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or '').lower()
        return (host == 'linkedin.com' or host.endswith('.linkedin.com')) and (
            '/posts/' in parsed.path or '/feed/update/' in parsed.path or '/pulse/' in parsed.path
        )
    except ValueError:
        return False

@st.cache_data(ttl=900, show_spinner=False)
def bing_search(term, freshness):
    query = f'site:linkedin.com/posts/ "{term}"'
    if freshness != 'Any time':
        query += ' ' + {'Last 7 days': 'past week', 'Last 30 days': 'past month', 'Last 90 days': 'past 3 months'}[freshness]
    endpoint = 'https://www.bing.com/search?' + urlencode({'q': query, 'format': 'rss'})
    response = requests.get(endpoint, headers={'User-Agent': 'Mozilla/5.0 (compatible; TechnicalResearch/1.0)'}, timeout=20)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    records = []
    for item in root.findall('./channel/item'):
        link = (item.findtext('link') or '').strip()
        if not is_post(link):
            continue
        records.append({
            'Keyword': term,
            'Title': clean_html(item.findtext('title')),
            'Snippet (search preview)': clean_html(item.findtext('description')),
            'Post URL': link,
            'Search publication date (unverified)': item.findtext('pubDate') or '',
            'Collected UTC': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'),
        })
    return records

with st.form('search_form'):
    keywords = st.text_area('Keywords (one per line)', DEFAULT, height=145)
    col1, col2 = st.columns(2)
    with col1:
        freshness = st.selectbox('Search recency hint (not a verified post-date filter)', ['Any time', 'Last 7 days', 'Last 30 days', 'Last 90 days'], index=2)
    with col2:
        limit = st.number_input('Maximum results to display', 5, 200, 50, step=5)
    submitted = st.form_submit_button('Search public posts', type='primary')

if 'results' not in st.session_state:
    st.session_state.results = pd.DataFrame()

if submitted:
    terms = list(dict.fromkeys(t.strip() for t in keywords.splitlines() if t.strip()))[:15]
    if not terms:
        st.warning('Enter at least one keyword.')
    else:
        rows, failures = [], []
        with st.spinner('Searching public indexes…'):
            for term in terms:
                try:
                    rows.extend(bing_search(term, freshness))
                except (requests.RequestException, ET.ParseError) as exc:
                    failures.append(f'{term}: {type(exc).__name__}')
        df = pd.DataFrame(rows)
        if not df.empty:
            df['canonical'] = df['Post URL'].str.split('?', n=1).str[0].str.rstrip('/')
            df = df.drop_duplicates(subset=['canonical']).drop(columns='canonical').head(int(limit)).reset_index(drop=True)
        st.session_state.results = df
        if failures:
            st.warning('Some searches failed: ' + '; '.join(failures))
        if df.empty:
            st.info('No publicly indexed LinkedIn post URLs were returned. Try broader keywords or Any time. Search indexing and RSS availability vary.')

results = st.session_state.results
if not results.empty:
    st.success(f'Found {len(results)} unique publicly indexed post links.')
    st.dataframe(results, use_container_width=True, hide_index=True, column_config={'Post URL': st.column_config.LinkColumn('Post URL')})
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        results.to_excel(writer, sheet_name='Public Post Leads', index=False)
        pd.DataFrame({'Important notes': [
            'These are search-result previews, not verified full LinkedIn posts.',
            'Dates shown are RSS/search dates and may not match LinkedIn publication dates.',
            'The search engine may return zero results or change its RSS behavior.',
            'Verify each source before citing or sharing any technical claims.',
        ]}).to_excel(writer, sheet_name='Read Me', index=False)
    st.download_button('⬇️ Download Excel', data=buffer.getvalue(), file_name='linkedin_post_leads.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

st.divider()
st.info('This free MVP discovers public post links and search snippets. It does not read private LinkedIn posts, guarantee complete post text, verify authors/dates, or use a paid AI API. Search-engine results are incomplete and can change.')
