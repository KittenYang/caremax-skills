# CareMax Skills — Examples

## Quick Start

After installing the skill, just say any of the following to your agent:

```
Show all my health indicators
What's my creatinine level?
Blood sugar trend over the past 6 months
Do I have any abnormal indicators?
Show my recent check-up reports
Search for liver function related reports
Help me scan this medical report (with image)
Show my mom's blood sugar trend
```

## Conversation Examples

### Example 1: Query Indicator Trend

```
User: How's my creatinine been lately?

Agent:
  → bash api-call.sh GET /api/skill/indicators
  → Finds "Creatinine" indicator (id: abc-123)
  → bash api-call.sh GET "/api/skill/indicators/trend?id=abc-123"
  → Returns:
    Your creatinine trend over the past 6 months:
    - 2025-01-15: 88 μmol/L (normal, ref: 44-133)
    - 2025-03-20: 95 μmol/L (normal, ref: 44-133)
    - 2025-06-10: 102 μmol/L (normal, ref: 44-133)
    Slight upward trend but all within normal range.
```

### Example 2: Upload & OCR a Medical Report

```
User: [sends a photo of a blood test report]

Agent:
  → bash api-call.sh POST /api/skill/upload (uploads file)
  → bash api-call.sh POST /api/skill/ocr '{"fileIds":["file-001"]}'
  → Returns:
    Extracted from your blood routine report (2025-06-15, City Hospital):
    - Hemoglobin: 145 g/L (normal)
    - White blood cells: 11.2 × 10⁹/L (HIGH, ref: 3.5-9.5)
    - Platelets: 230 × 10⁹/L (normal)
    ⚠️ White blood cell count is elevated. Consider consulting your doctor.
```

### Example 3: Semantic Search

```
User: Have I had any abnormal liver function results?

Agent:
  → bash api-call.sh POST /api/skill/records/search '{"query":"abnormal liver function"}'
  → Returns:
    Found 2 reports with liver function abnormalities:
    - 2025-02-10 (City Hospital): ALT 65 U/L (HIGH, ref: 7-40)
    - 2024-11-05 (University Hospital): GGT 58 U/L (HIGH, ref: 10-50)
```

### Example 4: Family Member Query

```
User: Show my mom's blood sugar trend

Agent:
  → bash api-call.sh GET /api/skill/members
  → Finds "Mom" (id: member-456, relationship: parent)
  → bash api-call.sh GET "/api/skill/indicators?memberId=member-456"
  → Finds "Blood Glucose" → gets trend
  → Returns trend data
```

### Example 5: First-time Authentication (automatic)

```
User: Show my blood routine

Agent:
  → bash api-call.sh GET /api/skill/indicators → returns no_credentials
  → bash auth-flow.sh (auto: opens browser + polls)
  → "I've opened the authorization page. Please log in and click Allow."
  → (user completes in browser)
  → auth-flow.sh detects approval, saves token
  → bash api-call.sh GET /api/skill/indicators → returns data
  → Displays blood routine indicators
```
