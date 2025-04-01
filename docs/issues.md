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
     question: model we're using (llama 3:70B) supports 8192 tokens but we're getting input too long at 6975 tokens. 

3. Vedanta: list index out of range
4. Info edge: dialogues referenced before assignment - fixed
    Todo: fix the (cid:45) thing that appears in places where ti and in are supposed to be.
5. GAIL: list index oor
6. siemens: dialogues
7. tata motors: fails silently, no output, mgmt extract fine
8. reliance - filenames are mmgmt
9.  airtel - file names are mgmt
10. bajaj finserv - takes forever to load