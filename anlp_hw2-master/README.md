# Pittsburgh/CMU Domain-Specific RAG System

## Overview

This project implements a **Retrieval-Augmented Generation (RAG)** system specifically designed to answer questions about **Pittsburgh** and **Carnegie Mellon University (CMU)**. The system enhances the capabilities of large language models (LLMs) by retrieving relevant context from a specialized knowledge base before generating answers to domain-specific queries. This allows the system to provide more accurate and informed responses in areas such as university history, local events, culture, and sports.

## Features

- **Domain-specific knowledge retrieval**: The system can retrieve information related to Pittsburgh and CMU from a curated knowledge base.
- **Comparison of model architectures**: We evaluate three different model architectures to understand the impact of varying retrieval strategies on performance.
- **Performance evaluation**: The system is compared against closed-book approaches to assess its ability to provide accurate responses.
- **Error analysis and model improvement**: An in-depth analysis of model errors provides insights into performance differences and potential improvements.

## Data

The knowledge base includes information on the following topics:

- **General Information about Pittsburgh/CMU**: Basic facts and details about the city and university.
- **History of Pittsburgh and CMU**: Key historical events and milestones.
- **Events in Pittsburgh and on Campus**: Information about notable events in Pittsburgh and CMU events, including academic, cultural, and sporting events.
- **Music and Culture**: Data about the music scene, arts, and cultural heritage in Pittsburgh and CMU.
- **Sports**: Details about sports teams, events, and historical data related to athletics at CMU and Pittsburgh.

## Models

We evaluated three different approaches to enhance the retrieval-augmented generation process:

- **Model 1**: Basic retrieval with QA pairs. This approach retrieves relevant question-answer pairs from the knowledge base to generate responses.
- **Model 2**: Enhanced retrieval with QA pairs. This model improves upon Model 1 by including additional context or processed information to enhance retrieval accuracy.
- **Model 3**: Raw knowledge chunk retrieval. This model retrieves raw knowledge chunks (unstructured data) from the knowledge base, offering a more flexible and detailed retrieval mechanism for generating answers.

## Project Structure and Usage

Follow the steps below to run the project effectively:

1. **Data Scraping**: 
   - Description: Contains various scraping functions tailored specifically for different websites, determining the depth of scraping based on website structure to ensure completeness.

   - Output: Scraped data is saved into the `knowledge_resource` folder.
   
   Execution:
   `web_scraping_general_event` folder
   
3. **Data Cleaning**:
   - Description: Clean and preprocess data obtained from scraping. This ensures data consistency and suitability for training and retrieval.

   - Handled in: `ANLP_hw2_pipeline.ipynb`

4. **QA Pair Generation**:
   - Description: Generates Question-Answer pairs using the T5 model after experimentation with several methods, including Mistral, GPT-2, and Phi-2. Final choice: T5 model.

   - Handled in: `ANLP_hw2_pipeline.ipynb`

5. **RAG System Implementation**:
   - Description: Implements the retrieval-augmented generation model leveraging the generated QA pairs and knowledge base for answering queries.

   - Handled in: `ANLP_hw2_pipeline.ipynb`

6. **Evaluation**:
   - Description: Evaluates RAG system performance against baseline closed-book models. Performs error analysis to improve future iterations.

   - Handled in: `ANLP_hw2_pipeline.ipynb`

You can follow the steps in the notebook to run each part of the pipeline and observe the results.
