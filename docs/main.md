# Understanding the main module of Concall summarizer

use this to fix import errors
``` bash
export PYTHONPATH=/home/kakashi/build/concall/Concall-summarizer
/home/kakashi/build/concall/.venv/bin/python /home/kakashi/build/concall/Concall-summarizer/backend/main.py
```


Imports: Classify moderator intent, extract management


Goal: Understand the flow of data in detail, operations being done, the final state of data and intermediate states while processing so that I can improve existing processes, generalize for different documents and handle edge cases.

Edge cases encountered (unfixed):
1. In certain documents, there are no moderators and no management details stated in first or second page and no analyst discussion. We need to be able to extract names of all management people and map their respective dialogues.
2. We need to clean headers and footers of each page transcript, to prevent text like 'page 2 of 15' or name of company in headers or other text in headers or footers from showing up in the main text. This reduces quality of the data. 

## Flow of data

1. Pdf document path used to load document, converted to text using pdfplumber, stored in a page number: page text mapping.
2. Init conference call parser - initializes a regex pattern to extract who the speaker is, current_analyst and last_speaker to None (Useful while keeping track in conversations).
3. Remove extra spaces, normalize case (clean_text).
4. extract_company_name : Extracts the company name from the letter on the first page. May not work for all documents, as all do not have the letter. Can probably try something else, like searching headers of the page. This approach likely requires an LLM though, as names would have no significant pattern there.
5. extract_management_team : Takes in a page, uses the ExtractManagement processor to do an LLM call on the page and return the management personnel of the company participating in the call (usually on first and second page, but may not be specified in rare cases).
6. extract_dialogues : Creates three types of dialogues out of the given transcript of call.



## Questions

1. Line 60 in main.py: why are we doing self.speaker? won't that return false for the first instance that a person is talking?
   1. If this fails - extract speaker, if that fails, assume it is the last speaker continuing and append to that text.
   2. But till what point? How do we know if a new speaker has started speaking?
2. Line 104 in main.py: What is matches? What does finditer do and what is the for loop doing here?