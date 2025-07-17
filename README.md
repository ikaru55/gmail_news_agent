## Gmail New Agent: Your Personal AI Email Summarizer
Welcome to Gmail New Agent! 👋 This is a smart agent that automatically fetches, translates, and summarizes important emails from your Gmail inbox. Using the power of Google's Gemini API, it creates concise reports from newsletters and news alerts, and then emails you the summary.

This project is designed to run seamlessly on Google Cloud Run and can be scheduled to run at any interval you choose, ensuring you always stay updated without the clutter.
<img width="995" height="951" alt="Gemini_Generated_Image_ocq5c7ocq5c7ocq5" src="https://github.com/user-attachments/assets/d6d13d56-60e0-47b1-8346-d3315abce881" />

## ✨ Features
Selective Email Fetching: Monitors your Gmail for unread emails from a specific list of senders you define.

AI-Powered Summarization: Leverages the Google Gemini API to read, translate, and summarize the content of multiple emails into a single, coherent report.

Custom Prompts: The AI's behavior is guided by a system prompt that you can customize to fit your needs (e.g., "Summarize these investment news articles for my morning brief").

Automated Email Reports: Once the summary is ready, the agent automatically sends it to your specified email address.

Secure Authentication: Uses OAuth 2.0 to securely interact with the Gmail API, ensuring your account's safety.

Containerized & Serverless: Packaged with a Dockerfile for easy deployment on serverless platforms like Google Cloud Run.

Scheduled Execution: Includes instructions for setting up Google Cloud Scheduler to run your agent automatically (e.g., every morning).

## ⚙️ How It Works
Trigger: The agent is triggered either by an HTTP request or a scheduled job.

Fetch Emails: It securely connects to your Gmail account and finds unread emails from your target senders (TARGET_SENDER).

Process Content: The subject and body of each email are extracted.

Generate Summary: All the email content is sent to the Gemini API with a specific prompt. Gemini then creates a summary based on your instructions.

Send Report: The final summary is sent as a new email to your designated recipient address (RECIPIENT_EMAIL).

Mark as Read: To avoid processing the same emails again, the agent marks the original emails as "read."

## 🚀 Setup and Deployment Guide
Follow these steps to get your own Gmail New Agent up and running.

### Part 1: Initial Local Setup
1. Prerequisites
Python 3.10 or higher.

A Google Cloud Platform (GCP) account with billing enabled.

A Google account (Gmail).

2. Clone the Repository
Bash
~~~
git clone https://github.com/your-username/gmail-new-agent.git
cd gmail-new-agent
~~~
3. Install Dependencies
Bash
~~~
pip install -r requirements.txt
~~~
4. Configure Google Cloud & Gmail API
This is the most crucial step. You need to authorize the application to access your Gmail.

Create a Google Cloud Project: Go to the Google Cloud Console and create a new project.

Enable the Gmail API: In your new project, go to "APIs & Services" > "Library" and search for "Gmail API". Click Enable.

Configure OAuth Consent Screen:

Go to "APIs & Services" > "OAuth consent screen".

Choose External and click "Create".

Fill in the required fields (App name, User support email, Developer contact information).

On the "Scopes" page, click "Add or Remove Scopes", search for Gmail API, and add all of the following:
~~~
https://www.googleapis.com/auth/gmail.readonly

https://www.googleapis.com/auth/gmail.send

https://www.googleapis.com/auth/gmail.modify
~~~
On the "Test users" page, add the Google account email you want the agent to access.

Create Credentials:

Go to "APIs & Services" > "Credentials".

Click "+ CREATE CREDENTIALS" and select OAuth client ID.

For "Application type", select Desktop app.

Give it a name and click "Create".

A popup will appear. Click DOWNLOAD JSON.

Rename the downloaded file to credentials.json and place it inside the gmail_helper/ directory.

5. Get Your Gemini API Key
Go to the Google AI Studio.

Click "Create API key" and copy your new key.

6. Run Locally to Generate token.json
Before deploying, you must run the app once locally to authorize its access to your Gmail.

Configure the App:

Open main.py and set the RECIPIENT_EMAIL to the address where you want to receive the summaries. You can also adjust the TARGET_SENDER list.

Run the Authentication Flow:

Execute the main.py script from your terminal.

Bash
~~~
python main.py
~~~
A new browser tab will open, asking you to log in with your Google account (the one you added as a test user).

Grant the requested permissions.

After successful authorization, a new file named token.json will be created in the gmail_helper/ directory. This file stores your authorization token.

IMPORTANT: credentials.json and token.json contain sensitive information. Make sure they are listed in your .gitignore file and are never committed to your public repository.

### Part 2: Deploy to Google Cloud Run
1. Submit the Build
This command builds a Docker image of your application and stores it in the Google Artifact Registry.

Bash
~~~
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/gmail-new-agent
Replace YOUR_PROJECT_ID with your actual Google Cloud Project ID.
~~~
2. Deploy to Cloud Run
This command deploys your container and sets up the necessary environment variable for your Gemini API key.

Bash
~~~
gcloud run deploy gmail-new-agent \
  --image gcr.io/YOUR_PROJECT_ID/gmail-new-agent \
  --platform managed \
  --region YOUR_REGION \
  --allow-unauthenticated \
  --set-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest"
~~~
Replace YOUR_PROJECT_ID and YOUR_REGION (e.g., us-central1).
The --allow-unauthenticated flag is needed so that Cloud Scheduler can easily trigger it.

The --set-secrets command securely provides your Gemini API key to the application. It assumes you have already stored the key in Secret Manager with the name GEMINI_API_KEY. If not, do that first in the Google Cloud Console.

### Part 3: Schedule with Google Cloud Scheduler
Finally, let's automate the agent to run on a schedule.

Go to Cloud Scheduler: In the Google Cloud Console, navigate to Cloud Scheduler.

Create a Job: Click CREATE JOB.

Define the Job:

Name: Give your job a name (e.g., daily-email-summary).

Region: Select the same region where you deployed your Cloud Run service.

Frequency: Define how often you want the job to run using a cron expression. For example, to run it at 8 AM every day, use: 0 8 * * *.

Timezone: Select your timezone.

Configure the Execution:

Target type: Select HTTP.

URL: Enter the URL of your deployed Cloud Run service. You can find this on the Cloud Run page in the console.

HTTP method: Select GET.

Click "Create".

That's it! Your agent is now fully deployed and will automatically run on the schedule you defined, delivering neat email summaries right to your inbox. Enjoy your clutter-free life! 🎉
