# Concall Parser

**Concall Parser** is an open-source Python library designed to efficiently extract insights from earnings call (concall) transcripts. It enables seamless extraction of management commentary, analyst discussions, company information, and more.

---

## 📦 Installation

Install the library using pip:

```bash
pip install concall-parser
```


## Usage

You can initialize the ConcallParser either with a local PDF path or directly via a URL to the concall document.

### Using a Local PDF

```python
from concall_parser.parser import ConcallParser

parser = ConcallParser(path="path/to/concall.pdf")
```

### Using a PDF Link

```python
from concall_parser.parser import ConcallParser

parser = ConcallParser(link="https://www.bseindia.com/xml-data/corpfiling/AttachHis/458af4e6-8be5-4ce2-b4f1-119e53cd4c5a.pdf")
```

## Configuration

The library leverages GROQ for core NLP tasks such as intent classification. To use GROQ, ensure the following environment variables are set:

```bash
export GROQ_API_KEY="YOUR GROQ API KEY"
export GROQ_MODEL="YOUR GROQ MODEL NAME"
```

We by default use llama3-70b-8192 if any groq supported models are not provided.


## ✨ Features

Concall parser lets you extract whatever you want from a concall. You can extract the management commentary, analyst discussion, and other details like company name and management names present in the concalls.

### Extract Management Team

```python
parser.extract_management_team()
```

### Extract Management Commentary

```python
parser.extract_commentary()
```

### Extract Analyst Discussion

```python
parser.extract_analyst_discussion()
```

###  Extract All Details

```python
parser.extract_all()
```


## 🤝 Contributing

We welcome contributions! If you'd like to improve this library or report issues, please feel free to submit a pull request or open an issue.

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.
