from datetime import datetime
from elasticsearch import Elasticsearch
import hashlib
import io
import requests
import docx

def clean_line(line):
    return line.strip().strip('\uFEFF')

def read_faq(file_id):
    url = f'https://docs.google.com/document/d/{file_id}/export?format=docx'
    response = requests.get(url)
    response.raise_for_status()
    
    with io.BytesIO(response.content) as f_in:
        doc = docx.Document(f_in)

    questions = []
    question_heading_style = 'heading 2'
    section_heading_style = 'heading 1'
    
    section_title = ''
    question_title = ''
    answer_text_so_far = ''
     
    for p in doc.paragraphs:
        style = p.style.name.lower()
        p_text = clean_line(p.text)
    
        if len(p_text) == 0:
            continue
    
        if style == section_heading_style:
            section_title = p_text
            continue
    
        if style == question_heading_style:
            answer_text_so_far = answer_text_so_far.strip()
            if answer_text_so_far != '' and section_title != '' and question_title != '':
                questions.append({
                    'text': answer_text_so_far,
                    'section': section_title,
                    'question': question_title,
                })
                answer_text_so_far = ''
    
            question_title = p_text
            continue
        
        answer_text_so_far += '\n' + p_text
    
    answer_text_so_far = answer_text_so_far.strip()
    if answer_text_so_far != '' and section_title != '' and question_title != '':
        questions.append({
            'text': answer_text_so_far,
            'section': section_title,
            'question': question_title,
        })

    return questions

def generate_document_id(doc):
    combined = f"{doc['course']}-{doc['question']}-{doc['text'][:10]}"
    hash_object = hashlib.md5(combined.encode())
    hash_hex = hash_object.hexdigest()
    return hash_hex[:8]

# Connect to Elasticsearch
es = Elasticsearch(['http://localhost:9200'])

# Generate index name
index_name_prefix = 'documents'
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
index_name = f"{index_name_prefix}_{current_time}"
print("index name:", index_name)

# Define index settings
index_settings = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "text": {"type": "text"},
            "section": {"type": "text"},
            "question": {"type": "text"},
            "course": {"type": "keyword"},
            "document_id": {"type": "keyword"}
        }
    }
}

# Create index
es.indices.create(index=index_name, body=index_settings)

# Read FAQ documents
faq_documents = {
    'llm-zoomcamp': '1qZjwHkvP0lXHiE4zdbWyUXSVfmVGzougDD6N37bat3E'
}

documents = []
for course, file_id in faq_documents.items():
    course_documents = read_faq(file_id)
    documents.append({'course': course, 'documents': course_documents})

last_document = None

# Index documents
for course_dict in documents:
    for doc in course_dict['documents']:
        doc['course'] = course_dict['course']
        doc['document_id'] = generate_document_id(doc)
        es.index(index=index_name, id=doc['document_id'], body=doc)
        last_document = doc

# Print the last document
print("Last document:")
print(last_document)

# Print the last document ID
if last_document:
    print("Last document ID:", last_document['document_id'])
else:
    print("No documents were indexed")
