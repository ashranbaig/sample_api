# from flask import Flask, request, jsonify
# from functions import UPSCPipeline
# import json

# app = Flask(__name__)

# # Initialize the pipeline
# pipeline = UPSCPipeline(
#     form_recognizer_endpoint="https://theabhyas.cognitiveservices.azure.com/",
#     form_recognizer_api_key="FT7QD74jYWlBEXuoGJFCtztmCRGXo5rBe2tCrpm9e9TDCJVmUIVmJQQJ99AKACGhslBXJ3w3AAALACOGvTKX",
#     openai_api_key="c7d0d93d93904a68b9e2d96e4cdabbcf",
#     openai_api_version="2023-05-15",
#     openai_endpoint="https://ict-openai-heromotocorp.openai.azure.com/",
#     openai_deployment_name= "gpt-4o-ict"
# )


# @app.route('/process-pipeline', methods=['POST'])
# def process_pipeline():
#     """
#     Endpoint to process the entire pipeline: extract, filter, and summarize.
#     """
#     try:
        
#         if 'file' not in request.files:
#             return jsonify({"error": "No file part in the request"}), 400
        
        
#         uploaded_file = request.files['file']

        
#         file_content = uploaded_file.read()

        
#         extracted_text = pipeline.extract_text_from_pdf(file_content)
        
        
#         filtered_text = pipeline.filter_upsc_related_articles(extracted_text)
        
#         # print(filtered_text)
        
#         summary = pipeline.summarize_merged_articles(filtered_text)

#         print("summary...........",summary)
        
#         # print("extracted_text11111111111", extracted_text)

#         extracted_date = pipeline.extract_date_from_header(extracted_text)

    
#         return jsonify({
#             "summary": summary,
#             "date": extracted_date
#         })

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=False)

from flask import Flask, request, jsonify
from functions import UPSCPipeline
from flask import request
import json

app = Flask(__name__)


pipeline = UPSCPipeline(
    form_recognizer_endpoint="https://theabhyas.cognitiveservices.azure.com/",
    form_recognizer_api_key="FT7QD74jYWlBEXuoGJFCtztmCRGXo5rBe2tCrpm9e9TDCJVmUIVmJQQJ99AKACGhslBXJ3w3AAALACOGvTKX",
    openai_api_key="2Zw5NhTjTn3Fp7uBnwU0yhgVJNmutUkwPQ6GtuDi7EK6cOa2jEgsJQQJ99AKACYeBjFXJ3w3AAABACOGPrtE",
    openai_api_version="2024-02-15-preview",
    openai_endpoint="https://azopenaiabhyas.openai.azure.com/",
    openai_deployment_name="gpt-4o-mini"
)

# def reformat_summary(raw_summary):
#     """
#     Converts the raw summary string into a list of structured JSON objects.
#     """
#     articles = raw_summary.split("Headline:")
#     structured_summary = []

#     for article in articles[1:]:  # Skip the first split part (it's empty)
#         lines = article.strip().split("\n")
        
#         # Extract Headline
#         headline = ""
#         article_summary = ""
#         key_points = []

#         for line in lines:
#             line = line.strip()
#             if not line:
#                 continue
#             if line.startswith("Article Summary:"):
#                 article_summary = line.replace("Article Summary:", "").strip()
#             elif line.startswith("Headline:"):
#                 headline = line.replace("Headline:", "").strip()
#             elif line.startswith("-"):
#                 key_points.append(line.strip(" ,"))
#             else:
#                 # If no explicit prefix, assume it's part of the headline
#                 if not headline:
#                     headline = line.strip()

#         structured_summary.append({
#             "Headline": headline,
#             "Article Summary": article_summary,
#             "Key Points": key_points
#         })

#     return structured_summary

def reformat_summary(raw_summary):
    """
    Converts the raw summary string into a list of structured JSON objects.
    Handles cases where Key Points may not have consistent formatting or spacing.
    """
    articles = raw_summary.split("Headline:")
    structured_summary = []

    for article in articles[1:]:  
        lines = article.strip().split("\n")
        
        
        headline = ""
        article_summary = ""
        key_points = []
        collecting_keypoints = False  

        for line in lines:
            line = line.strip()
            if not line:  
                continue
            
            if line.startswith("Article Summary:"):
                article_summary = line.replace("Article Summary:", "").strip()
                collecting_keypoints = False
            elif line.startswith("Headline:"):
                headline = line.replace("Headline:", "").strip()
                collecting_keypoints = False
            elif line.lower().startswith("key points"): 
                collecting_keypoints = True
            elif collecting_keypoints:
                
                if line.endswith(","):
                    key_points.append(line.rstrip(",").strip())
                else:
                    key_points.append(line.strip())
            else:
                
                if not headline:
                    headline = line.strip()

        structured_summary.append({
            "Headline": headline,
            "Article Summary": article_summary,
            "Key Points": key_points
        })

    return structured_summary


# @app.route('/process-pipeline', methods=['POST'])
# def process_pipeline():
#     """
#     Endpoint to process the entire pipeline: extract, filter, and summarize.
#     """
#     try:
#         if 'file' not in request.files:
#             return jsonify({"error": "No file part in the request"}), 400

#         uploaded_file = request.files['file']
#         file_content = uploaded_file.read()

        
#         extracted_text = pipeline.process_file(file_content)
#         filtered_text = pipeline.filter_upsc_related_articles(extracted_text)
#         raw_summary = pipeline.summarize_merged_articles(filtered_text)
#         print(raw_summary)
#         extracted_date = pipeline.extract_date_from_header(extracted_text)

        
#         structured_summary = reformat_summary(raw_summary)

#         return jsonify({
#             "date": extracted_date,
#             "summary": structured_summary
#         })

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=False)

from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

def extract_text_from_json(json_file_obj):
    """
    Extracts text from the uploaded JSON file.
    :param json_file_obj: File-like object (uploaded JSON file)
    :return: Extracted text from the JSON
    """
    
    data = json.load(json_file_obj)

    
    extracted_text = ""

    
    if "pages" in data:
        for page in data["pages"]:
            
            page_number = page.get("pageNumber", "Unknown Page")
            extracted_text += f"Page {page_number}:\n"

           
            if "lines" in page:
                for line in page["lines"]:
                    extracted_text += line.get("content", "") + "\n"

            extracted_text += "\n" 
    else:
        return "Key 'pages' not found in JSON."

    return extracted_text

@app.route('/process-pipeline', methods=['POST'])
def process_pipeline():
    """
    Endpoint to process the entire pipeline: extract, filter, and summarize.
    """
    try:
       
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        uploaded_file = request.files['file']

        
        if uploaded_file.filename == '':
            return jsonify({"error": "No selected file"}), 400

       
        extracted_text = extract_text_from_json(uploaded_file)

        
        filtered_text = pipeline.filter_upsc_related_articles(extracted_text)
        raw_summary = pipeline.summarize_merged_articles(filtered_text)
        print(raw_summary)
        extracted_date = pipeline.extract_date_from_header(extracted_text)

       
        structured_summary = reformat_summary(raw_summary)

      
        return jsonify({
            "date": extracted_date,
            "summary": structured_summary
        })

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format in the uploaded file"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False)
