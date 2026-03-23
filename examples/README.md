# CareMax Skills — Examples

## Agent Conversation Examples

### Example 1: Query Health Indicator Trend

```
User: "What's my creatinine level been like recently?"

Agent:
1. GET /api/skill/indicators → finds "Creatinine" (id: abc-123)
2. GET /api/skill/indicators/trend?id=abc-123
3. Returns:
   Your creatinine trend over the past 6 months:
   - 2025-01-15: 88 μmol/L (normal, ref: 44-133)
   - 2025-03-20: 95 μmol/L (normal, ref: 44-133)
   - 2025-06-10: 102 μmol/L (normal, ref: 44-133)
   Slight upward trend but all within normal range.
```

### Example 2: Upload and OCR a Medical Report

```
User: [sends a photo of a blood test report]

Agent:
1. POST /api/skill/upload → fileIds: ["file-001"]
2. POST /api/skill/ocr → { fileIds: ["file-001"] }
3. Returns:
   Extracted from your blood routine report (2025-06-15, City Hospital):
   - Hemoglobin: 145 g/L (normal)
   - White blood cells: 11.2 × 10⁹/L (HIGH, ref: 3.5-9.5)
   - Platelets: 230 × 10⁹/L (normal)
   ⚠️ White blood cell count is elevated. Consider consulting your doctor.
```

### Example 3: Semantic Search

```
User: "Have I had any abnormal liver function results?"

Agent:
1. POST /api/skill/records/search → { query: "abnormal liver function" }
2. Returns:
   Found 2 reports with liver function abnormalities:
   - 2025-02-10 (City Hospital): ALT 65 U/L (HIGH, ref: 7-40)
   - 2024-11-05 (University Hospital): GGT 58 U/L (HIGH, ref: 10-50)
```

### Example 4: Family Member Query

```
User: "Show my mom's blood sugar trend"

Agent:
1. GET /api/skill/members → finds "Mom" (id: member-456, relationship: parent)
2. GET /api/skill/indicators?memberId=member-456 → finds "Blood Glucose"
3. GET /api/skill/indicators/trend?id=glucose-uuid
4. Returns the trend data for the parent member
```

## First-Time Setup Example

```
User: "Connect to my CareMax account"

Agent:
1. POST /api/auth/device → { device_code: "dc-xxx", user_code: "ABCD-1234" }
2. Opens browser: https://api.caremax.ai/authorize?code=ABCD-1234
3. "I've opened a browser window. Please log in and click 'Allow' to authorize."
4. Polls /api/auth/device/token every 5 seconds...
5. "Connected! I can now access your health data."
```
