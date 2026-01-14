from flask import Flask, render_template, request
from jobspy import scrape_jobs
import pandas as pd
import re

app = Flask(__name__)

def extract_contacts(description):
    """Scans description for Emails and Phone Numbers."""
    if not isinstance(description, str):
        return None, None
    
    # Regex for Emails
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = list(set(re.findall(email_pattern, description)))
    
    # Regex for Phone Numbers (Indian & Intl)
    phone_pattern = r'(?:\+91[\-\s]?)?[6789]\d{4}[\-\s]?\d{5}|0\d{2,4}[\-\s]?\d{6,8}'
    phones = list(set(re.findall(phone_pattern, description)))

    return emails, phones

@app.route('/', methods=['GET', 'POST'])
def index():
    jobs_data = []
    search_term = ""
    location = ""
    
    if request.method == 'POST':
        search_term = request.form.get('job_title')
        location = request.form.get('location')
        
        try:
            # Scrape LinkedIn, Indeed, and Glassdoor
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "glassdoor"],
                search_term=search_term,
                location=location,
                results_wanted=20, 
                hours_old=72,
                country_indeed='india'
            )
            
            if not jobs.empty:
                for index, row in jobs.iterrows():
                    emails, phones = extract_contacts(row.get('description', ''))
                    
                    # Identify the site based on the URL or the scraper data
                    site_name = row.get('site', 'Unknown') 
                    
                    jobs_data.append({
                        'title': row.get('title'),
                        'company': row.get('company'),
                        'location': row.get('location'),
                        'url': row.get('job_url'),
                        'site': site_name,  # Passing the site name (indeed, linkedin, etc.)
                        'emails': emails,
                        'phones': phones,
                        'has_contact': bool(emails or phones)
                    })
                    
        except Exception as e:
            print(f"Error: {e}")

    return render_template('index.html', jobs=jobs_data, search_term=search_term, location=location)

if __name__ == '__main__':

    app.run(debug=True, port=5000)
