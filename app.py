from flask import Flask, render_template, request
from jobspy import scrape_jobs
import pandas as pd
import re

app = Flask(__name__)

def extract_contacts(description):
    """Scans description for Emails and Phone Numbers."""
    if not isinstance(description, str):
        return None, None
    
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = list(set(re.findall(email_pattern, description)))
    
    phone_pattern = r'(?:\+91[\-\s]?)?[6789]\d{4}[\-\s]?\d{5}|0\d{2,4}[\-\s]?\d{6,8}'
    phones = list(set(re.findall(phone_pattern, description)))

    return emails, phones

@app.route('/', methods=['GET'])
def index():
    jobs_data = []
    # Get parameters from URL (e.g., ?job_title=Flutter&page=2)
    search_term = request.args.get('job_title', '')
    location = request.args.get('location', '')
    page = int(request.args.get('page', 1))  # Default to page 1
    
    # Configuration
    RESULTS_PER_PAGE = 10  # Keep this low (10-15) to prevent Timeouts!
    offset = (page - 1) * RESULTS_PER_PAGE

    if search_term and location:
        try:
            # Scrape with Offset (Pagination)
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed"], # Glassdoor is very slow, removed for speed
                search_term=search_term,
                location=location,
                results_wanted=RESULTS_PER_PAGE, 
                offset=offset, # <--- This handles the pagination
                hours_old=72,
                country_indeed='india'
            )
            
            if not jobs.empty:
                for index, row in jobs.iterrows():
                    emails, phones = extract_contacts(row.get('description', ''))
                    site_name = row.get('site', 'Unknown') 
                    
                    jobs_data.append({
                        'title': row.get('title'),
                        'company': row.get('company'),
                        'location': row.get('location'),
                        'url': row.get('job_url'),
                        'site': site_name,
                        'emails': emails,
                        'phones': phones,
                        'has_contact': bool(emails or phones)
                    })
                    
        except Exception as e:
            print(f"Error: {e}")

    # Calculate next/prev page numbers
    next_page = page + 1
    prev_page = page - 1 if page > 1 else None

    return render_template('index.html', 
                         jobs=jobs_data, 
                         search_term=search_term, 
                         location=location, 
                         page=page, 
                         next_page=next_page, 
                         prev_page=prev_page)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

