# Concall Parser

**Concall Parser** is an open-source Python library designed to efficiently extract insights from earnings call (concall) transcripts. It enables seamless extraction of management commentary, analyst discussions, company information, perfect for building financial research tools, summarizers, or investor dashboards.

Check out the repo at [Github](https://github.com/JS12540/concall-parser/).

---

**Note:** We currently support earnings calls of Indian companies (BSE, NSE registered) only.

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

Or just pass in the values when creating the parser object.

```python
parser = ConcallParser(path="path/to/concall.pdf", groq_api_key=your_api_key, groq_model=preferred_groq_model)
```


We use llama3-70b-8192 as the default model if any groq supported models are not provided as env.

## ✨ Features

Concall Parser enables structured extraction of key insights from earnings call transcripts. You can extract management commentary, analyst discussions, company name, management details, and more—streamlined for downstream analysis or integration.

### Extract Concall Info like Management and Company Name

```python
parser.extract_concall_info()
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

## Example Data structure

```json
{
    "concall_info": {
        "company_name": "SKF India Limited", // company name will come as value
        "Mukund Vasudevan": "Managing Director", // management name will come as key and designation will come as value
    },
    "commentary": [
        {
            "speaker": "Ashish Pruthi",
            "dialogue": "thank you. good morning, everyone. thank you for joining us today. today with us, we have skf india's managing director, mr. mukund vasudevan and our cfo, mr. ashish saraf. before i turn the call over to the management, i would like to remind you that in this call, some of the remarks contain forward-looking statements, which are subject to risks and uncertainties and actual results may differ materially we can now open the call for q&a."
        }
    ],
    "analyst_discussion" : {
        "Mukesh Saraf" : {
            "analyst_company" : "Avendus Spark",
            "dialogue" : [
                {
                    "speaker": "Mukesh Saraf",
                    "dialogue": "my first question is on the revenue mix. so could you kind of give us some details on the different segments like the auto, industrial, exports and probably within that, some of the subsegments as well."
                },
                {
                    "speaker": "Mukund Vasudevan",
                    "dialogue": "all right. i'll let ashish saraf, my cfo, answer that in terms of so that he can share precise numbers."
                },
            ]
        }
    }
}
```

## Concalls not supported yet

Concalls which do not contain analyst dicusssion and are more of press release like Reliance are not supported yet. If you find any concall that is not being parsed correctly, please open an issue with the label `doc unsupported`.

## 🤝 Contributing

We welcome contributions! If you'd like to improve this library or report issues, please feel free to submit a pull request or open an issue.

You can find detailed contributing guidelines here: [CONTRIBUTING.md](https://github.com/JS12540/concall-parser/blob/main/CONTRIBUTING.md)


## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.


## 🎯 Downstream Tasks

Here are some potential downstream tasks where `concall-parser` can be highly valuable:

| Task | Description |
|------|-------------|
| **Sentiment Analysis** | Analyze the tone (positive/negative/neutral) of management commentary to assess confidence or caution. |
| **Named Entity Recognition (NER)** | Extract structured entities such as company names, executive names, analyst firms, and competitors. |
| **Competitor Benchmarking** | Compare commentary and strategy across companies in the same sector for peer analysis. |
| **Intent Classification** | Categorize analyst questions by topic (financials, operations, market outlook, etc.). |
| **Knowledge Base Generation** | Populate internal tools or dashboards with structured Q&A and insights from concalls. |
| **QoQ Change Tracking** | Monitor changes in management messaging and strategy across earnings calls. |
| **Earnings Call Summarization** | Automatically generate concise summaries for quick understanding of the concall. |
