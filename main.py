import re

import pdfplumber

# Path to the uploaded PDF
pdf_path = "d9791ed3-f139-4c06-8750-510adfa779eb.pdf"

# Lists to store extracted information
management_people = []
dialogues = {}

# Patterns to identify key sections
date_pattern = re.compile(
    r"Date:\s*(\d{1,2}\w{2}\s+\w+\s+\d{4})", re.IGNORECASE
)
company_pattern = re.compile(r"([A-Z\s]+LIMITED)", re.IGNORECASE)
management_pattern = re.compile(
    r"MR\. (\w+\s+\w+).*?–\s*(.*?–\s*SKF INDIA LIMITED)", re.IGNORECASE
)
speaker_pattern = re.compile(r"(?P<speaker>[A-Za-z\s]+):\s(?P<dialogue>.+)")

# Variables to store extracted data
conference_date = None
company_name = None
current_speaker = None

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            # Extract Date
            date_match = date_pattern.search(text)
            if date_match and not conference_date:
                conference_date = date_match.group(1)

            # Extract Company Name
            company_match = company_pattern.search(text)
            if company_match and not company_name:
                company_name = company_match.group(1).strip()

            # Extract Management People
            for match in management_pattern.findall(text):
                management_people.append({"Name": match[0], "Role": match[1]})

            # Extract Dialogues
            for line in text.split("\n"):
                speaker_match = speaker_pattern.match(line)
                if speaker_match:
                    current_speaker = speaker_match.group("speaker").strip()
                    dialogue = speaker_match.group("dialogue").strip()
                    if current_speaker not in dialogues:
                        dialogues[current_speaker] = []
                    dialogues[current_speaker].append(dialogue)
                elif current_speaker:
                    dialogues[current_speaker][-1] += (
                        " " + line.strip()
                    )  # Append to last dialogue for continuity

# Print extracted results
print("Conference Date:", conference_date)
print("Company Name:", company_name)
print("Management People:", management_people)
print("Dialogues:", dialogues)
