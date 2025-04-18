# Data Description

We are working with **unstructured earnings call transcripts (concalls)**, in PDF format. These documents are sourced from publicly listed companies and include both **scripted commentary** and **interactive Q&A sessions**. However, the formatting and content style of these transcripts vary significantly, making it challenging to extract structured data consistently.


This document outlines the **generic structure**, **common entities**, **important contexts**, and known **document variations** to aid development and debugging.

---

## Generic Format

The most common format follows a structure similar to transcripts from **Adani Total Gas Ltd.**, and is described below. Most other transcripts deviate slightly from this structure, requiring our pipeline to be robust to such inconsistencies.

### Structure:

1. **Introductory Page(s)**  
   - Contains a formal letter or boilerplate intro with date, subject, disclaimers, or a short agenda.  
   - *Not relevant* for our extraction use cases.

2. **Management Info Page**  
   - Contains the **company name** and a list of **management personnel** attending the call, often with their **designations**.

3. **Transcript**  
   - Main body of the concall, which includes:
     - **Moderator introductions**
     - **Management commentary**
     - **Analyst Q&A session**

---

## Entity Types

We primarily deal with three kinds of speaker entities:

1. **Moderator**  
   - Opens and closes the call, introduces speakers, and manages transitions.  
   - Useful for **segmenting** the transcript and detecting **context shifts**.

2. **Management**  
   - Core speakers from the company (e.g., CEO, CFO, Directors).  
   - Their speech includes:
     - **Performance commentary** (historical insights)
     - **Outlook/future plans**
     - **Responses to analyst queries**

3. **Analysts**  
   - Represent investment firms and ask questions during the Q&A session.  
   - Each analyst's segment usually includes their **name**, **company**, and **questions**.

---

## Context Types

We are interested in three major content segments for downstream analysis:

### 1. Management Commentary
   - Often includes multiple speakers from the management.
   - Provides:
     - **Business performance** summaries
     - **Operational highlights**
     - **Macroeconomic commentary**
     - **Future strategy and projections**

### 2. Analyst Q&A
   - Typically follows the commentary.
   - Format:  
     `Analyst:` *asks question(s)*  
     `Management:` *responds*  
   - Useful for:
     - Discovering recurring concerns
     - Extracting FAQs
     - Generating investor-facing summaries
    
### 3. Company management 
   - Names and designations of company management participating in the meeting.

---

## Document Variations

Here are known deviations across documents observed so far. Handling these is key to making the pipeline robust and generalizable:

| Variation | Description | Example/Impact |
|----------|-------------|----------------|
| **No Moderator** | Entire call is handled by management; no moderator cues. | Harder to detect context shifts. |
| **No Analyst Section** | Only management commentary is present. | Must gracefully skip Q&A extraction. |
| **Moderator Named Differently** | Specific name used instead of “Moderator.” | E.g., “Host,” “Operator,” actual name |
| **Management List Missing** | No list of names/designations provided at the beginning. | Need to infer roles from the conversation. |
| **Single Management Speaker** | Only one person speaks on behalf of the company. | Simplifies role mapping but affects Q&A identification. |
| **Inline Speaker Labels** | Speaker name appears inline, without a newline or indentation. | E.g., “John Doe: Thank you for the question...” |
