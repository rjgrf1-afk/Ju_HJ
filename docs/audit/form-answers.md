# YouTube API Audit form - answers

Form: https://support.google.com/youtube/contact/yt_api_form?hl=en
Turn off browser auto-translate. Never put passwords, client secrets or tokens in the form.

## Section 1: Request Type
- Complete a compliance audit to request for additional quota

## Section 2: Organization and Contact Information
- Full legal name: (your real name)
- Organization legal name: Individual (or your name)
- Parent company: Individual
- Organization website: https://rjgrf1-afk.github.io/Ju_HJ/
- Country: South Korea / Address, City, Postal code: (your contact address)
- Organization size/type: Independent developer / Sole proprietor
- Primary contact name / email: (your name) / (your Google account email)
- Primary technical contact: check "Same as primary contact"

## Section 3: Business Model and Google Contacts
- Describe your organization's YouTube-related work:

  I am an individual YouTube creator running the channel "눈썰미 연구소" (@nunsseulmi_lab, channel ID UC7DlQBmVmLFcLiquvUfvKLw). I make one original "find the odd one out" puzzle Short every day. The API client is a private script used only by me: it uploads each day's Short to my own channel with videos.insert, schedules it to publish at 18:00 KST, and reads my own channel's statistics (YouTube Analytics) so I can improve the content. It is not offered to any other user and does not access other channels' data.

- Target audience: Internal users
- How does the API client monetize: Free service (no charge to users)
- Google Partner Manager / YouTube Partner Manager: None
- How did you first hear about the YouTube Data API: Google developer documentation
- Content Owner ID: (leave empty)
- Linked YouTube channel URL: https://www.youtube.com/@nunsseulmi_lab
- Google Ads customer ID: (leave empty)

## Section 4: API Client Overview and Access Information
- API client name: 눈썰미 연구소 업로더
- Does the name include "YouTube": No
- Primary access URL: https://rjgrf1-afk.github.io/Ju_HJ/
- Privacy policy URL: https://rjgrf1-afk.github.io/Ju_HJ/privacy.html
- Terms of service URL: https://rjgrf1-afk.github.io/Ju_HJ/terms.html
- Is the API client publicly accessible: No
- Demo account username / password / login URL: (leave empty)
- Special access instructions:

  No login or demo account: this is a private command-line script used only by the channel owner. Source code: https://github.com/rjgrf1-afk/Ju_HJ/tree/ccr-aaca7a09-rdvvku/shorts . Screenshots of the OAuth flow, an upload and the analytics report are included in the attached PDF.

- Required acknowledgement checkbox: check

## Section 5: Use Case and Quota Extension Details
- Number of projects: 1
- Google Cloud project number: 203046541838
- Use case categories: Video upload and account management; Analytics and reporting
- Does the API client require users to sign in with Google (OAuth): Yes
- Derived metrics / data retention policy agreement: check
- Estimated API usage: the lowest option
- Endpoints checkbox: check, then youtube.videos.insert
  - Daily total quota: 1600
  - Maximum quota per minute: 1600
  - Detailed justification:

    One upload per day to my own channel (@nunsseulmi_lab). One videos.insert call costs up to 1,600 units, so 1,600 units per day is enough. No retries or bulk uploads.

- Total quota requested for project #1: No change / default quota (10,000)

## Section 6: Additional Evidence
Upload docs/audit/all-evidence.pdf (16 pages, 1.5 MB) in the first file field.
If other required file fields block submission, upload the same PDF there.
The PDF contains: privacy policy screenshot, homepage screenshot, terms of service,
architecture diagram, user flow diagram, conditional evidence (OAuth flow, upload, analytics)
and the complete upload script shorts/upload.py (pages 15-16).

## Section 7: Attestation and Submit
Check all attestations, complete reCAPTCHA, Submit.
