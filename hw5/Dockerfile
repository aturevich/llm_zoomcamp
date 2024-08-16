FROM elasticsearch:8.15.0

USER root

# # Install Python and pip using microdnf
# RUN microdnf update -y && microdnf install -y python3 python3-pip

# Install Python Elasticsearch client and other necessary libraries
RUN pip install elasticsearch python-docx requests

# Copy our Python script into the container
COPY indexing_script.py /

# Switch back to elasticsearch user
USER elasticsearch

# Set the entry point to run Elasticsearch and then our Python script
ENTRYPOINT ["/bin/bash", "-c", "elasticsearch -d && sleep 30 && python3 /indexing_script.py"]
