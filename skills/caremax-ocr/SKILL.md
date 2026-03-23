---
name: caremax-ocr
description: "Upload medical reports and run OCR recognition via CareMax Health API. Use when a user wants to upload a health report image or PDF, scan a medical document, extract data from a check-up report, or digitize paper health records. Trigger terms: upload report, scan report, OCR, recognize report, extract indicators, digitize medical report, health report image, check-up photo."
license: MIT
---

# CareMax Upload & OCR

This skill handles uploading medical report files (PDF, JPG, PNG) and extracting structured data via OCR. The process is always two steps: upload first, then OCR.

## Step 1: Upload Report

```http
POST /api/skill/upload
Authorization: Bearer sk-caremax-...
Content-Type: multipart/form-data

file: <binary file data>
memberId: <optional member UUID>
```

Supported formats: PDF, JPG, JPEG, PNG.

Response:
```json
{
  "fileIds": ["file-uuid-1", "file-uuid-2"]
}
```

PDF files with multiple pages may return multiple file IDs (one per page image).

## Step 2: OCR Recognition

```http
POST /api/skill/ocr
Authorization: Bearer sk-caremax-...
Content-Type: application/json

{
  "fileIds": ["file-uuid-1"],
  "memberId": "member-uuid",
  "redo": false
}
```

Parameters:
- `fileIds` (required) — File IDs from the upload step
- `memberId` (optional) — Associate with a family member
- `redo` (optional) — Re-run OCR on previously processed files

Response contains extracted medical records:
```json
{
  "records": [
    {
      "test_date": "2025-03-15T00:00:00",
      "hospital": "Peking University Third Hospital",
      "department": "Laboratory",
      "report_title": "Blood Routine",
      "has_abnormality": 1,
      "indicators": [
        {
          "name": "hemoglobin",
          "value": "135",
          "unit": "g/L",
          "reference_range": "130-175",
          "is_abnormal": 0
        }
      ]
    }
  ]
}
```

## Complete Workflow

When a user says "help me scan this report" or shares an image:

1. **Upload**: `POST /api/skill/upload` with the file
2. **OCR**: `POST /api/skill/ocr` with the returned file IDs
3. **Present**: Show extracted data — hospital, date, indicators with values and reference ranges
4. Highlight any abnormal indicators

## OCR Quota

- Free users: limited OCR scans per month
- Premium users: unlimited OCR
- If quota exceeded, the API returns an error — inform the user about upgrading

## Tips

- For best OCR results, ensure the image is clear and well-lit
- The OCR engine handles Chinese medical reports natively
- Extracted indicators are automatically standardized and linked to the user's indicator dictionary
- After OCR, the data is immediately queryable via the records and indicators endpoints
