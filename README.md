# Policy Analysis Tool

## Overview
This Policy Analysis Tool is designed to analyze public sentiment on government policies by fetching and analyzing comments from Reddit. It offers an interactive web interface for selecting policies, displays analyzed data, and generates downloadable PDF reports.

## Features
- **Interactive Selection of Government Policies**: Users can select from a pre-loaded list of government policies to analyze.
- **Automatic Data Fetching from Reddit**: Leverages Reddit's API to fetch relevant discussion threads and comments.
- **Sentiment Analysis**: Utilizes a generative AI model to classify sentiments of the comments into positive, negative, or neutral.
- **Top Ideas & Concerns**: Also show the top ideas and top concerns given by public on selected policy. 
- **PDF Report Generation**: Summarizes the analysis results in a structured PDF report, which includes sentiment distribution and excerpts of comments.
- **Cached Data Display**: For select policies, displays previously analyzed and cached data for quicker access.

## Technology Stack
- **Python**: Primary programming language used.
- **PyWebIO**: Used for creating the interactive web interface.
- **PRAW (Python Reddit API Wrapper)**: Facilitates the fetching of data from Reddit.
- **ReportLab**: Utilized for generating PDF reports.
- **Flask**: Serves as the backend framework to manage web interactions.

## Installation
To set up the project locally, follow these steps:

```bash
# Clone the repository
git clone https://github.com/your-github-username/policy-analysis-tool.git

# Navigate to the project directory
cd policy-analysis-tool

# Install required Python libraries
pip install -r requirements.txt

```
## Code Explanation

### Main Functions
- **`load_policy_names()`**: Reads policy names from a CSV file, providing a list for the dropdown menu in the user interface.
- **`reddit_authenticate()`**: Configures the Reddit API client using credentials stored in environment variables to ensure secure API calls.
- **`fetch_posts_and_comments()`**: Retrieves relevant comments from Reddit using the PRAW library, specifically targeting comments related to the selected policy. Filters out removed and bot-generated comments for cleaner data.
- **`get_policy_context()`**: Extracts contextual information about policies from a JSON file, which aids in understanding and analyzing comments more effectively.
- **`create_pdf()`**: Generates a PDF report detailing the analysis results, including statistical summaries and representative comments.
- **`download_pdf()`**: Provides functionality for users to download the generated PDF reports directly from the web interface.

### Web Interface
- **`home_screen()`**: Displays the initial landing page of the application where users can start the analysis by selecting a government policy from a dropdown menu.
- **`display_data()`**: Presents the analysis results on the web interface, including sentiment analysis and comments visualization.
- **`main()`**: The central function that drives the application, handling policy selection, data fetching, analysis, and rendering of results.

## Contribution
All the team memebers have contributed equally.
- **Gaurav** and **Kirtan** worked on LLM model selection, model preperation and backend part.
- **Jayshil** and **Amit Prajapati** worked on data preprocessing, created csv and json for further use and frontend/UI part.
- **Ankur** and **Rohit Gupta** worked on data gathering from different trusted sorces, project report and PPT.

## License
Distributed under the MIT License. See `LICENSE` for more information.


