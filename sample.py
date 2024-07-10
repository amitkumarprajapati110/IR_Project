import json
import praw
import os
import google.generativeai as genai
import pywebio
from flask import Flask, request, jsonify
from pywebio.session import set_env, download
from fpdf import FPDF, XPos, YPos
from pywebio.input import *
from pywebio.output import *
from pywebio import session
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import io
import csv


def load_policy_names(csv_file_path):
    policy_names = []
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            policy_names.append(row['Scheme'])  # Assuming 'Scheme' is the column header
    return policy_names



def reddit_authenticate():
    client_id = os.getenv('REDDIT_CLIENT_ID', 'vanpv5Jb8hzPQyzOaprQVg')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET', 'IlmwYBJsLqo1SYEMwCQjY-6QqkXXtw')
    user_agent = os.getenv('REDDIT_USER_AGENT', 'script by u/Apprehensive-Fee4041')
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        reddit.auth.scopes()
        return reddit
    except Exception as e:
        print("ERROR: Failed to authenticate with Reddit", e)
        raise


def fetch_posts_and_comments(reddit, subreddit_name, query):
    try:
        subreddit = reddit.subreddit(subreddit_name)
        comments = []
        for post in subreddit.search(query, sort='relevance', time_filter='all', limit=10):
            post.comments.replace_more(limit=0)
            comments.extend([comment.body for comment in post.comments.list()[:26] if
                             comment.body not in ('[removed]', '[deleted]') and 'bot' not in comment.body])
        return comments
    except Exception as e:
        print(f"ERROR: An error occurred: {e}")
        raise


def get_policy_context(filename, policy_name):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            data = {key.lower(): value for key, value in data.items()}
            return data[policy_name.lower()]
    except KeyError as e:
        toast(f"Context of the Policy :{policy_name} not found ", color='error')
        home_screen()
        print(f"KeyError: '{policy_name}' not found in '{filename}'.")
        raise
    except Exception as e:
        print(f"ERROR: An error occurred while fetching the policy context: {e}")
        raise

def safe_text(text):
    """Encodes the text to Latin-1, replacing errors with a placeholder."""
    return text.encode('latin-1', 'replace').decode('latin-1')

def create_pdf(data, filename='report.pdf'):
    # Using an in-memory buffer to store PDF data
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setTitle("Report Summary")
    pdf.setFont("Helvetica", 12)
    y_position = height - 72  # Start position on the page

    # Header
    pdf.drawString(72, y_position, "Report Summary")
    y_position -= 30

    # Basic data output
    pdf.drawString(72, y_position, f"Total Comments: {data['total_comments']}")
    y_position -= 15
    pdf.drawString(72, y_position, f"Infavor: {data['infavor']}%")
    y_position -= 15
    pdf.drawString(72, y_position, f"Against: {data['against']}%")
    y_position -= 30

    # Sections with comments
    for section, comments in data.items():
        if section not in ['total_comments', 'infavor', 'against']:
            pdf.drawString(72, y_position, section + ':')
            y_position -= 15
            pdf.setFont("Helvetica", 10)
            for comment in comments:
                pdf.drawString(82, y_position, comment)
                y_position -= 15
                if y_position < 100:  # Check if we need a new page
                    pdf.showPage()
                    y_position = height - 72
                    pdf.setFont("Helvetica", 12)

    pdf.save()
    buffer.seek(0)
    return buffer

def download_pdf(data,filename):
    buffer = create_pdf(data, filename)
    put_file(filename, buffer.getvalue(), 'Download PDF Report')

def home_screen():
    """This function represents the home screen of the application."""
    clear()  # Clear the screen
    put_markdown("## Policy Analysis Tool")
    put_buttons(['Start Analysis'], onclick=lambda _: main())

def display_data(policy_name,data):
    put_html(f"<h2>{policy_name}</h2>")
    # put_html("</br>")
    put_html("<h3>Total Comments</h3>")
    put_html("<h1>" + str(data["total_comments"]) + "</h1>")

    put_html("<h3>Infavor States</h3>")
    put_html("<h4>" + str(data["infavor"]) + "%</h4>")

    put_html("<h3>Against States</h3>")
    put_html("<h4>" + str(data["against"]) + "%</h4>")

    put_html("<h3>Positive Comments</h3>")
    for comment in data["positive_comments"]:
        # put_html("<ul>" + "".join(f"<li>{line}</li>" for line in comment.split("\n") if line.strip()) + "</ul>")
        put_html("<ul><li>" + comment + "</li></ul>")

    put_html("<h3>Negative Comments</h3>")
    for comment in data['negative_comments']:
        # put_html("<ul>" + "".join(f"<li>{line}</li>" for line in comment.split("\n") if line.strip()) + "</ul>")
        put_html("<ul><li>" + comment + "</li></ul>")

    put_html("<h3>Ideas and Suggestions</h3>")
    for comment in data['ideas_suggestions']:
        # put_html("<ul>" + "".join(f"<li>{line}</li>" for line in comment.split("\n") if line.strip()) + "</ul>")
        put_html("<ul><li>" + comment + "</li></ul>")

    put_html("<h3>Concerns</h3>")
    for comment in data['concerns']:
        # put_html("<ul>" + "".join(f"<li>{line}</li>" for line in comment.split("\n") if line.strip()) + "</ul>")
        put_html("<ul><li>" + comment + "</li></ul>")

    # Setup the download button
    # put_buttons(['Download PDF Report'], onclick=[lambda: download_pdf(data,"Generated_Report.pdf")])
    put_buttons(['Download PDF Report'], onclick=lambda _: download_pdf(data, "Generated_Report.pdf"))

    # put_buttons(['Go to Home Screen'], onclick=home_screen)
    put_buttons(['Go to Home Screen'], onclick=lambda _: home_screen())

def main():
    clear()
    csv_file_path = 'D:\College\M.Tech\Semester-1\FCS\Assignments\Assignment-1\IRProject\GovtPolicyList.csv'
    # Set environment options
    set_env(auto_scroll_bottom=True)
    # policy_name = request.args.get('policy_name')
    # Ask for the policy name
    policy_names = load_policy_names(csv_file_path)
    # policy_name = input("Enter the policy name:")
    # # Ask for the policy name from a dropdown
    # policy_name = select("Select the policy name:", options=policy_names)
    # # Use 'select()' with the 'searchable=True' attribute for a searchable dropdown list
    # policy_name = select(label="Type and select a policy name:", options=policy_names, searchable=True)
    # Use the 'input()' function with 'datalist' for autocomplete
    policy_name = input("Type and select a policy name:", datalist=policy_names, required=True)

    # Check if the entered name is one of the policies in the dropdown after submission
    if policy_name not in policy_names:
        toast("Please select a valid policy name from the dropdown.", color='error')
        home_screen()
        return
    if not policy_name:
        toast("Policy name is required.", color='error')
        return

    if policy_name == "Pradhan Mantri Jan Dhan Yojana":
        # Load and display the data from the JSON file
        with open('data.json', 'r') as json_file:
            data = json.load(json_file)
            display_data(policy_name,data)
            return

    try:
        toast("Authenticating with Reddit...", color='info')
        reddit_api = reddit_authenticate()
        toast("Fetching posts and comments...", color='info')
        all_comments = fetch_posts_and_comments(reddit_api, "all", policy_name)
        filename = 'government_policies.json'  # Ensure this file is accessible, adjust path as necessary


        policy_context = get_policy_context(filename, policy_name)


        # Atep 1: Configure genai with the API key
        GOOGLE_API_KEY = "AIzaSyBQvjtdFcLCHANDFdNl4ugQV1u0ZV7fgv8"
        genai.configure(api_key=GOOGLE_API_KEY)

        # Step 2: Import the model (LLM- gemini-pro)
        model = genai.GenerativeModel('gemini-pro')

        # Pass user input government policy name and its context to our model as a context along with the question
        context_to_learn = f"Learn the following government policy thoroughly and understand its context. The following is the context that I want the model to learn.\nThe name of the policy is {policy_name} and the following is the policy context: {policy_context}"
        final_comments = []
        all_filtered_comments = {'positive': [], 'negative': []}
        for comment in all_comments:
            # question = f"Say 'Relevant' or 'Irrelevant' only by checking whether the comment '{comment}' is relevant or irrelevant to the policy: '{context_to_learn}'?"
            question = f"Say 'Positive', 'Negative' or 'Neutral' by checking whether the comment '{comment}' is positive or negative or netural about the policy: '{context_to_learn}'?"
            toast("Analyzing comments...", color='info')
            response = model.generate_content(context_to_learn + "\n" + question)
            # print(response.text)
            if (response.text.lower() == 'positive'):
                all_filtered_comments['positive'].append(comment)
                final_comments.append(comment)
                print(f"Positive COMMENT FOUND: {comment}")
            elif (response.text.lower() == 'negative'):
                all_filtered_comments['negative'].append(comment)
                final_comments.append(comment)
                print(f"Negative COMMENT FOUND: {comment}")

        print(
            f"\nTotal comments post-filtering: {len(all_filtered_comments['positive']) + len(all_filtered_comments['negative'])}\n")

        # Placeholder for comments filtering logic
        positive_comments = all_filtered_comments['positive']
        negative_comments = all_filtered_comments['negative']

        infavor = round((len(all_filtered_comments['positive']) / (len(all_filtered_comments['positive']) + len(all_filtered_comments['negative']))) * 100)
        against = round((len(all_filtered_comments['negative']) / (len(all_filtered_comments['positive']) + len(all_filtered_comments['negative']))) * 100)

        # # Filtering comments - assuming use of a generative model or similar logic
        # # This section is hypothetical and needs actual implementation
        # positive_comments = [comment for comment in all_comments if 'good' in comment]
        # negative_comments = [comment for comment in all_comments if 'bad' in comment]

        ideas_concerns = {'Idea/Suggestion': [], 'Concern': []}
        list_coments = []
        for comment in final_comments:
            # question = f"Say 'Relevant' or 'Irrelevant' only by checking whether the comment '{comment}' is relevant or irrelevant to the policy: '{context_to_learn}'?"
            question = f"Say 'Idea/Suggestion', 'Concern', 'Both' or 'Neutral' by checking whether the comment '{comment}' is 'Idea/Suggestion', 'Concern', 'Idea and Concern Both' or 'netural' about the policy: '{context_to_learn}'?"
            toast("Identifying ideas and concerns...", color='info')
            response = model.generate_content(context_to_learn + "\n" + question)
            list_coments.append(response)
            if (response.text.lower() == 'idea' or response.text.lower() == 'suggestion'):
                ideas_concerns['Idea/Suggestion'].append(comment)
                list_coments.append(comment)
            elif (response.text.lower() == 'concern'):
                ideas_concerns['Concern'].append(comment)
                list_coments.append(comment)
            elif (response.text.lower() == 'both'):
                ideas_concerns['Idea/Suggestion'].append(comment)
                ideas_concerns['Concern'].append(comment)
                list_coments.append(comment)
            else:
                list_coments.append(comment)

        # return jsonify({
        #     'total_comments': len(all_comments),
        #     'positive_comments': positive_comments[:10],
        #     'negative_comments': negative_comments[:10],
        #     'ideas' : ideas_concerns['Idea/Suggestion'][:10],
        #     'concerns' : ideas_concerns['Concern'][:10],
        #     'infavor' : infavor,
        #     'against' : against
        # })
        # Organizing data for PDF generation
        data = {
            'total_comments': len(all_comments),
            'infavor': infavor,  # Example calculated value
            'against': against,  # Example calculated value
            'positive_comments': positive_comments[:10],
            'negative_comments': negative_comments[:10],
            'ideas_suggestions': ideas_concerns['Idea/Suggestion'][:10],
            'concerns': ideas_concerns['Concern'][:10]
        }
        # with open('data.json', 'w') as f:
        #     json.dump(data, f)

        clear()  # Clears the previous output
        # put_table([
        #     ['total_comments',len(all_comments)],
        #     ['positive_comments',positive_comments[:10]],
        #     ['negative_comments',negative_comments[:10]],
        #     ['ideas',ideas_concerns['Idea/Suggestion'][:10]],
        #     ['concerns',ideas_concerns['Concern'][:10]],
        #     ['infavor',infavor],
        #     ['against',against]
        # ])
        put_html(f"<h2>{policy_name}</h2>")
        # put_html("</br>")
        put_html("<h3>Total Comments</h3>")
        put_html("<h1>" + str(len(all_comments)) + "</h1>")

        put_html("<h3>Infavor States</h3>")
        put_html("<h4>" + str(infavor) + "%</h4>")

        put_html("<h3>Against States</h3>")
        put_html("<h4>" + str(against) + "%</h4>")

        put_html("<h3>Positive Comments</h3>")
        for comment in all_filtered_comments['positive']:
            # put_html("<ul>" + "".join(f"<li>{line}</li>" for line in comment.split("\n") if line.strip()) + "</ul>")
            put_html("<ul><li>" + comment + "</li></ul>")

        put_html("<h3>Negative Comments</h3>")
        for comment in all_filtered_comments['negative']:
            # put_html("<ul>" + "".join(f"<li>{line}</li>" for line in comment.split("\n") if line.strip()) + "</ul>")
            put_html("<ul><li>" + comment + "</li></ul>")

        put_html("<h3>Ideas and Suggestions</h3>")
        for comment in ideas_concerns['Idea/Suggestion']:
            # put_html("<ul>" + "".join(f"<li>{line}</li>" for line in comment.split("\n") if line.strip()) + "</ul>")
            put_html("<ul><li>" + comment + "</li></ul>")

        put_html("<h3>Concerns</h3>")
        for comment in ideas_concerns['Concern']:
            # put_html("<ul>" + "".join(f"<li>{line}</li>" for line in comment.split("\n") if line.strip()) + "</ul>")
            put_html("<ul><li>" + comment + "</li></ul>")

        # Setup the download button
        # put_buttons(['Download PDF Report'], onclick=[lambda: download_pdf(data,"Generated_Report.pdf")])
        put_buttons(['Download PDF Report'], onclick=lambda _: download_pdf(data, "Generated_Report.pdf"))

        # put_buttons(['Go to Home Screen'], onclick=home_screen)
        put_buttons(['Go to Home Screen'], onclick=lambda _: home_screen())


    except Exception as e:
        return jsonify({'error': str(e)}), 500



pywebio.start_server(main(),port=6666,debug=True)