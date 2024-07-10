from flask import Flask, request, jsonify
import json
import praw
import os
import google.generativeai as genai

from pywebio.input import *
from pywebio.output import *


app = Flask(__name__)


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
        print(f"KeyError: '{policy_name}' not found in '{filename}'.")
        raise
    except Exception as e:
        print(f"ERROR: An error occurred while fetching the policy context: {e}")
        raise


@app.route('/fetch_comments', methods=['GET'])
def fetch_comments():
    policy_name = request.args.get('policy_name')
    if not policy_name:
        return jsonify({'error': 'Policy name is required as a query parameter.'}), 400

    try:
        reddit_api = reddit_authenticate()
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

        infavour = round((len(all_filtered_comments['positive']) / (len(all_filtered_comments['positive']) + len(all_filtered_comments['negative']))) * 100)
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

        return jsonify({
            'total_comments': len(all_comments),
            'positive_comments': positive_comments[:10],
            'negative_comments': negative_comments[:10],
            'ideas' : ideas_concerns['Idea/Suggestion'][:10],
            'concerns' : ideas_concerns['Concern'][:10],
            'infavour' : infavour,
            'against' : against
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
