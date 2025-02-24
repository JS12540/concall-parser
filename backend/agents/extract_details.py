# ruff: noqa

from backend.constants import MODEL_NAME
from backend.utils.get_groq_responses import get_groq_response


DETAIL_CONTEXT = """
Analyze the earnings call transcript and extract key details about the company's recent historical performance. Specifically focus on:

1. Financial metrics and growth:
- Revenue, volume, and profit growth numbers
- Margin trends and changes
- Segment/category-wise performance
- Geographic performance
- Key ratios and operational metrics

2. Operational performance:
- Distribution and reach metrics
- Market share data
- Product mix changes
- Channel performance
- Manufacturing/capacity utilization

3. Business environment impacts:
- Raw material/input cost trends
- Pricing actions taken
- Competitive dynamics
- Market conditions affecting performance
- Any unusual events or one-time factors

4. Recent strategic initiatives:
- Major launches or campaigns
- Recent acquisitions/investments
- Distribution expansion efforts
- Cost optimization programs

For each point, extract specific numbers where available and note any significant year-on-year or sequential changes. Present the information in a clear, structured format.

Example of expected output format:
Financial Performance:
- Revenue grew X% YoY to Rs.Y driven by [factors]
- EBITDA margins at X% vs Y% last year due to [reasons]
etc.

Operational Highlights:
- Direct reach increased to X outlets from Y
- Category A grew X% while Category B grew Y%
etc."""


OUTLOOK_CONTEXT = """
Review the earnings call transcript and identify all forward-looking statements and management commentary about future plans and outlook. Focus on:

1. Growth plans and targets:
- Revenue/volume growth targets
- Margin expansion plans
- Market share goals
- Distribution/reach targets
- Category/segment growth expectations

2. Strategic initiatives:
- Planned product launches
- Marketing/branding initiatives
- Capacity expansion plans
- New market entry plans
- Digital/omnichannel strategies

3. Investment plans:
- Planned capex
- Acquisition strategy
- R&D investments
- Distribution investments
- Technology investments

4. Management commentary on:
- Industry outlook
- Raw material/cost expectations
- Competitive landscape
- Consumer trends
- Potential risks or challenges

5. Specific guidance provided:
- Short-term (next quarter) outlook
- Medium-term (1-2 year) targets
- Long-term strategic goals
- Any quantitative targets shared

Present the information grouped by timeframe (near-term vs medium/long-term) and level of certainty (committed plans vs exploratory initiatives).

Example of expected output format:
Near-term Plans (Next 12 months):
- Planning to add X new outlets in Y markets
- Expects margins to reach X% by [timeframe]
etc.

Strategic Initiatives (Long-term):
- Targeting X% market share in Y category by [year]
- Plans to enter X new markets over next Y years
etc."""


class ExtractInfo:
    async def get_details(text:str):
        """Get the metrics of current quarter growth."""
        messages = [
            {"role": "system", "content": DETAIL_CONTEXT},
            {"role": "user", "content": text},
        ]
        response = await get_groq_response(messages=messages, model=MODEL_NAME)
        return response
    
    async def get_future_outlook(text:str):
        """Get future outlook and expansion plans."""
        messages = [
            {"role": "system", "content": OUTLOOK_CONTEXT},
            {"role": "user", "content": text},
        ]
        response = await get_groq_response(messages=messages, model=MODEL_NAME)
        return response