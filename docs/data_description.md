# Data Description

We're dealing with unstructured documents (PDFs) of earnings calls (also referred to as conference calls, concalls) in this repo. These have many variations and quirks, which are described below, to enable better understanding during development and debugging.

## Generic format

The most generic (and most common) format is seen in the case of Adani Total Gas Ltd., which is described below. Other documents have slight variations over this format, which need to be taken care of, but we want a generic pipeline to automate things as much as possible.

The start of a document has a page for a letter intimidating the concall, this is not relevant to our use case.

The next page contains the name of the company and some of the management who will be participating in the call (along with their designations).

### Entities
Three types of entities in a document:
1. Moderator: Introduces people as they are about to speak, starts and ends the call. Useful for identifying when context has changed.
2. Management: The management personnel of the company who are speaking in this call. The speech by these guys is extremely important, as they define the prior performance of the company (previous period, for which the concall is happening) and tell us about the management's view on the future of the company (outlook). They also answer questions put forward by analysts on the company's performance and expected changes.
3. Analysts: Analysts from other companies (investment firms). They question the management on certain aspects of the company's performance.


### Contexts
Mainly two types of contexts that we are interested in:
1. Management talks: The part where only the management personnel are speaking (moderator may introduce people as they are about to speak). This part gives us insight about the past and an outlook of the company's future, predicted growth etc. This is divided into two subcategories:
	1. Management commentary  (details): Gives details of past performance, quarterly or half yearly performance.
	2. Outlook: Gives an indication of what the management sees the company doing in the future, and their viewpoint on how it will play out.
2. Analyst question answer: Each analyst asks a question, which leads to a conversation between them and a member of the management. This can be used as FAQs and also help to understand more details about the company. Each analyst QA session is quite short (<1 page of text).

# Variations
Here we discuss the different kinds of variations in the documents encountered so far:
1. No moderator (): Moderator is not present for the concall, The management people handle the call themselves.
2. No analyst ():
3. Moderator name used instead of "moderator" ():
4. Management names not provided at start of document ():
5. 