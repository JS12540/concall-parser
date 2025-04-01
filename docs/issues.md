## Issues faced

### Past


### Present

1. Asianpaints: list index out of range 
   (main.py, extract_dialogues:line 92, dialogues["commentary_and_future_outlook"][-1][
                                    "dialogue"
                                ] += (" " + leftover_text)
    Comments: No moderator present
    intent = None
    dialogues empty: should not be the case
    page skipped: dialogues empty

2. Unilever: Prompt too long
     fix: change model to be longer context size

3. Vedanta: list index out of range
4. Info edge: dialogues referenced before assignment
5. GAIL: list index oor
6. siemens: dialogues
7. tata motors: fails silently, no output, mgmt extract fine
8. reliance - filenames are mmgmt
9. airtel - file names are mgmt
10. bajaj finserv - takes forever to load