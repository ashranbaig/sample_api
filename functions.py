from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from openai import OpenAI
from openai import AzureOpenAI
import re
import io
from io import BytesIO
from PyPDF2 import PdfReader
import json


class UPSCPipeline:
    def __init__(self, form_recognizer_endpoint, form_recognizer_api_key, openai_api_key, openai_api_version, openai_endpoint, openai_deployment_name):
        """
        Initializes the UPSC Pipeline with necessary credentials and endpoints.
        """
        self.form_recognizer_client = DocumentAnalysisClient(
            endpoint=form_recognizer_endpoint,
            credential=AzureKeyCredential(form_recognizer_api_key)
        )
        self.openai_client = AzureOpenAI(
            api_key=openai_api_key,
            api_version=openai_api_version,
            azure_endpoint=openai_endpoint
        )
        self.openai_deployment_name = openai_deployment_name

    # def extract_text_from_pdf(self, pdf_content):
    
    #     poller = self.form_recognizer_client.begin_analyze_document(
    #         "prebuilt-document", pdf_content
    #     )
    #     result = poller.result()

    #     extracted_text = ""
    #     for page in result.pages:
    #         extracted_text += f"Page {page.page_number}:\n"
    #         for line in page.lines:
    #             extracted_text += line.content + "\n"
    #         extracted_text += "\n"

    #     return extracted_text

    # def extract_text_from_pdf(self, pdf_content):
    #     """
    #     Extracts text from a PDF using Azure Form Recognizer in 2-page batches.
    #     """
    #     pdf_stream = BytesIO(pdf_content)
    #     pdf_reader = PdfReader(pdf_stream)
    #     total_pages = len(pdf_reader.pages)

    #     extracted_text = ""

    #     for start_page in range(1, total_pages + 1, 2):
    #         end_page = min(start_page + 1, total_pages)

            
    #         pages = f"{start_page},{end_page}" if start_page != end_page else f"{start_page}"

    #         try:
    #             poller = self.form_recognizer_client.begin_analyze_document(
    #                 "prebuilt-document",  
    #                 document=pdf_content,
    #                 pages=pages  
    #             )
    #             result = poller.result()

    #             for page in result.pages:
    #                 extracted_text += f"Page {page.page_number}:\n"
    #                 for line in page.lines:
    #                     extracted_text += line.content + "\n"
    #                 extracted_text += "\n"
    #         except Exception as e:
    #             print(f"Error processing pages {pages}: {e}")

    #     return extracted_text

    def extract_text_from_json(json_file_path):
        # Open and load the JSON file
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        # Initialize a variable to hold extracted text
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

    def filter_upsc_related_articles(self, text_to_summarize):
        """
        Filters articles related to UPSC topics using Azure OpenAI.
        """
        system_message = """
        You are a filtering assistant tasked with recognizing and retaining only the newspaper articles related to specific UPSC syllabus topics. You will receive a text of newpaper with so many articles, each with a headline and full content. Your job is to:

            1. **Identify and retain** articles related to the UPSC syllabus topics listed below, keeping their headline and  text content exactly as given.
            2. **Exclude any irrelevant articles** that do not relate to the UPSC syllabus topics.
            3. For relevant articles, respond with the **headline** and **entire original content**, word-for-word, without summarizing, rephrasing, or modifying any part.

            Here are the UPSC syllabus topics to focus on:
            - **Qualifying Papers on Indian Languages and English**: comprehension, precise writing, vocabulary, short essays, translation.
            - **Paper I (Essay)**: Various essay topics of general interest.
            - **Paper II (General Studies I)**: Indian Heritage and Culture, History, Geography of the World and Society.
            - **Paper III (General Studies II)**: Governance, Constitution, Polity, Social Justice, International Relations.
            - **Paper IV (General Studies III)**: Technology, Economic Development, Biodiversity,Biotechnology, Environment, Security, Disaster Management.
            - **Paper V (General Studies IV)**: Ethics, Integrity, and Aptitude; public administration ethics, probity in governance, and case studies on these topics.

            Only respond with the unaltered headline and relevant articles. Discard unrelated articles.
        """
        """
        # You are an **intelligent filtering assistant** specifically tasked with identifying and retaining ONLY the newspaper articles that align with key topics in the UPSC syllabus. Your responsibilities are as follows:

        # 1. **Filter with precision:** Review the provided text containing multiple newspaper articles, each with a headline and its full content. Your job is to filter out and retain only the articles that are strictly relevant to specific UPSC syllabus topics listed below.
        
        # 2. **Exact preservation of content:** For each article that matches the UPSC syllabus topics, retain the **headline** and the **entire original article content** exactly as given. Do not summarize, rephrase, modify, or add any interpretations to the content. The retained articles must remain word-for-word as in the original.

        # 3. **Exclude irrelevant content:** Discard any articles that do not directly pertain to the UPSC syllabus topics, regardless of their quality or general relevance.
        
        # 4. ** Below is the given list of topics, strictly adhere to that list only while filtering the content.


        # ### UPSC Syllabus Topics for Filtering:
        # - **Language and Essay Topics:**
        # - **Qualifying Papers on Indian Languages and English:** comprehension, précis writing, vocabulary, short essays, and translation-related topics.
        # - **Paper I (Essay):** essays on topics of general interest, reflecting critical analysis and thoughtful perspectives.
        
        # - **General Studies Papers:**
        # - **Paper II (General Studies I):** Indian Heritage and Culture, History, Geography of the World and Society.
        # - **Paper III (General Studies II):** Governance, Constitution, Polity, Social Justice, and International Relations.
        # - **Paper IV (General Studies III):** Technology, Economic Development, Biodiversity, Biotechnology, Environment, Security, and Disaster Management.
        # - **Paper V (General Studies IV):** Ethics, Integrity, and Aptitude; public administration ethics, probity in governance, and related case studies.

        # in detailed syllabus:
        #     GS Paper 1: Indian Heritage and Culture, History and Geography of the World and Society
        #        **Indian Culture: Cover salient aspects of art forms, literature, and architecture from ancient to modern times.
        #        **Modern Indian History: Focus on significant events, personalities, and issues from the middle of the eighteenth century to the present. This includes:
        #                 -The Freedom Struggle with its various stages and contributors.
        #                 -Post-independence consolidation and reorganization of India.
        #         **World History: Cover significant events from the 18th century, such as:
        #                 -The industrial revolution, world wars, colonization, and decolonization.
        #                 -Political philosophies such as communism, socialism, and capitalism, and their societal impacts.
        #         **Indian Society: Discuss:
        #                 -Salient features of Indian society, its diversity, and roles of women, women’s organizations, and population-related issues.
        #                 -Problems of poverty, developmental issues, urbanization, and their solutions.
        #                 -Effects of globalization and social empowerment.
        #                 -Key issues like communalism, regionalism, secularism, and their impact on Indian society.
        #         **World Geography: Cover:
        #                 -The salient features of world’s physical geography.
        #                 -Distribution of natural resources globally and factors influencing the location of industries.
        #                 -Key geophysical phenomena such as earthquakes, tsunamis, volcanic activity, and cyclones.
        #                 -Changes in geographical features and their environmental impacts.

        #     GS Paper 2: Governance, Constitution, Polity, Social Justice and International Relations
        #         **Indian Constitution: Discuss the historical underpinnings, evolution, features, amendments, and the basic structure.
        #                 -Examine federalism, the devolution of powers, and challenges at various governance levels.
        #                 -Separation of powers, dispute redressal mechanisms, and comparison with other countries' constitutions.
        #             Parliament and State Legislatures: Explore their structure, functioning, powers, and issues arising.
        #         **Executive and Judiciary: Study their structure, functioning, and roles in the governance system.
        #         **Constitutional Bodies: Roles and responsibilities of various bodies such as the Election Commission, CAG, etc.
        #         **Government Policies and Welfare Schemes: Discuss:
        #             -Government policies for development, welfare schemes for vulnerable sections.
        #             -The role of NGOs, SHGs, and other organizations in the development sector.
        #             -Challenges in health, education, and poverty alleviation.
        #         **International Relations: Focus on India’s neighborhood relations, international groupings, and the impact of global politics.
        #            -Understand bilateral, regional, and global agreements involving India.
        #            -Study of global institutions, agencies, and their impact on India’s interests.

        #     GS Paper 3: Technology, Economic Development, Bio-diversity, Environment, Security and Disaster Management
        #         **Indian Economy: Cover issues related to economic planning, growth, development, and employment.
        #             -Focus on inclusive growth, budgeting, and issues arising from economic policies.
        #             -Discuss agriculture, farm subsidies, PDS, and technology’s role in aiding farmers.
        #             -Analyze infrastructure, energy, ports, railways, and investment models.
        #         **Science and Technology: Focus on innovations in IT, space, Biotechnology, and the role of intellectual property.
        #             -Address environmental pollution, conservation, and disaster management.
        #         **Security and Internal Security: Discuss internal security challenges, cyber security, organized crime, and terrorism.
        #             Study the role of security forces and agencies in managing border security and domestic challenges.
        #     GS Paper 4: Ethics, Integrity and Aptitude.
        #             **Ethics in Governance: Cover the essence and consequences of ethics in human actions and governance.
        #                 -Study human values, attitudes, and the influence of society and institutions.
        #                 -Focus on integrity, impartiality, objectivity, and empathy in public service.
        #             **Public Service Values: Explore the challenges of ethical governance, corruption, transparency, and accountability.
        #                 -Discuss case studies related to ethics, governance, and integrity in public administration.
        #                 -Study the role of moral philosophers and the impact of their contributions.

        
        # ### Key Instructions for Response:
        # - Retain only **relevant articles** by matching them against the topics above.
        # - For each retained article, respond only with:
        # 1. The **headline** (exact as given in the original).
        # 2. The **entire unaltered content** of the article.
        # - Completely exclude and omit unrelated articles without mentioning them in your response.

        # Your output must be a clean and concise collection of only the relevant articles' headlines and texts, as per the given criteria. **Do not include commentary, explanations, or summaries.**
        """
        response = self.openai_client.chat.completions.create(
            model=self.openai_deployment_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Newspaper articles: {text_to_summarize}"}
            ]
        )
        return response.choices[0].message.content

    def summarize_merged_articles(self, merged_articles):
        """
        Summarizes the filtered articles into structured exam preparation points using Azure OpenAI.
        """
        system_message = """

            summarize each news article with a headline and a detailed breakdown of all relevant points. The summary should be concise but comprehensive enough to cover all significant aspects, as this is intended for competitive exam preparation.
            
            Format:
            
            Headline:
            Article Summary: Briefly introduce the main point of the article.
            Key Points
            
            ## IMPORTANT INSTRUCTION- Do not include any special character like "**" with the headings Headline, Article Summary, and Key Points. keep them simple, plain and there should be no line space between the headings and the content. 

            Cover each significant aspect of the news, focusing on facts, legal points, impacts, and background details relevant to understanding the full context. Ensure each point is detailed enough to be helpful for exam preparation but remains concise.
            Example Response:
            
            Headline:
            LMV License Holders Can Drive Transport Vehicles Weighing Less Than 7,500 kg: SC,
            
            Article Summary: The Supreme Court of India has ruled that those holding a Light Motor Vehicle (LMV) license can legally operate transport vehicles with an unladen weight of up to 7,500 kg without needing an additional endorsement.

            Key Points:
            Supreme Court Ruling: This judgment clarifies that LMV license holders can drive certain transport vehicles within the weight limit, under Section 10(2)(e) of the Motor Vehicles Act.,
            Constitution Bench Decision: A five-judge Constitution Bench led by Chief Justice D.Y. Chandrachud issued the ruling, addressing ambiguity around LMV license scope.,
            Impact on Insurance Claims: This decision alleviates insurance claim issues for drivers and contests the stance of insurance companies that require specific endorsements for insurance claims in accidents involving transport vehicles.,
            Legal Interpretation: The ruling emphasized that skill requirements under the MV Act do not differ between LMV and certain transport vehicles within the specified weight.,
            Insurance Companies’ Argument Rejected: The court dismissed insurance companies' arguments that driving authorization impacts road safety, highlighting that fundamental skills are consistent across vehicle types.,
            Significance for Road Safety: The judgment strengthens the understanding that driving competency is uniform and challenges the notion that separate authorizations directly correlate with accident prevention.
            
            Generate summaries for each news article in this structured format
            
            
            """
           
        
        response = self.openai_client.chat.completions.create(
            model=self.openai_deployment_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Newspaper articles: {merged_articles}"}
            ]
        )
        return response.choices[0].message.content

    def process_pipeline(self, pdf_path):
        """
        Executes the full pipeline: extract, filter, and summarize.
        """
        print("Extracting text from PDF...")
        extracted_text = self.extract_text_from_pdf(pdf_path)
        print("Filtering relevant articles...")
        filtered_text = self.filter_upsc_related_articles(extracted_text)
        print("Summarizing filtered articles...")
        summary = self.summarize_merged_articles(filtered_text)
        return summary
        
    
    def extract_date_from_header(self, extracted_text):
        """
        Extracts the date from the newspaper's first page header based on the extracted text.
        Assumes that the extracted text is already available.
        """
        
        header_text = "\n".join(extracted_text.splitlines()[:15])

       
        # print("Header Text:", header_text)

        
        #date_pattern = r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2},\s\d{4}\b"
        date_pattern = r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2}(?:,\s\d{4})?\b"
        
        match = re.search(date_pattern, header_text, re.IGNORECASE)

        
        return match.group(0) if match else "Date not found in header"

if __name__ == "__main__":
    pipeline = UPSCPipeline(
        form_recognizer_endpoint="https://theabhyas.cognitiveservices.azure.com/",
        form_recognizer_api_key="FT7QD74jYWlBEXuoGJFCtztmCRGXo5rBe2tCrpm9e9TDCJVmUIVmJQQJ99AKACGhslBXJ3w3AAALACOGvTKX",
        openai_api_key="2Zw5NhTjTn3Fp7uBnwU0yhgVJNmutUkwPQ6GtuDi7EK6cOa2jEgsJQQJ99AKACYeBjFXJ3w3AAABACOGPrtE",
        openai_api_version="2024-02-15",
        openai_endpoint="https://azopenaiabhyas.openai.azure.com/",
        openai_deployment_name= "azopenaiabhyas"
    )

    
    pdf_path = r" "
    summary_output = pipeline.process_pipeline(pdf_path)
    print(summary_output)