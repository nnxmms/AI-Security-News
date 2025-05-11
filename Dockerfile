FROM python:3.11-alpine

# Labels
LABEL name="AI Security News"
LABEL maintainer="https://github.com/nnxmms"

# Add user
RUN adduser -D user

# Install requirements
RUN pip install --upgrade pip
RUN pip install flask
RUN pip install pymongo

# Copy files
ADD static /home/user/static
ADD templates /home/user/templates
COPY app.py /home/user/

# Environment Variables
ENV TZ="UTC"

# Change to non-root user
USER user

# Create directories
WORKDIR /home/user

# Run main.py
CMD ["python3", "app.py"]