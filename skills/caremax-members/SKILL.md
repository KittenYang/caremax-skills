---
name: caremax-members
description: "Manage family members in CareMax Health. Use when a user asks about family health tracking, switching between family member profiles, or viewing another family member's health data. Trigger terms: family member, member list, my family, switch member, family health, spouse health, child health, parent health."
license: MIT
---

# CareMax Family Members

This skill covers listing and working with family member profiles. CareMax supports tracking health data for multiple family members under one account.

## List Members

```http
GET /api/skill/members
Authorization: Bearer sk-caremax-...
```

Response:
```json
{
  "members": [
    {
      "id": "member-uuid",
      "name": "John",
      "gender": "male",
      "birth_date": "1990-05-15",
      "relationship": "self",
      "is_default": 1
    },
    {
      "id": "member-uuid-2",
      "name": "Jane",
      "gender": "female",
      "birth_date": "1992-08-20",
      "relationship": "spouse",
      "is_default": 0
    }
  ]
}
```

## Using Member ID in Other Queries

All data endpoints accept an optional `memberId` parameter to scope queries to a specific family member:

- `GET /api/skill/indicators?memberId=xxx`
- `POST /api/skill/records/query` with `{ "memberId": "xxx" }`
- `POST /api/skill/records/search` with `{ "memberId": "xxx" }`
- `POST /api/skill/upload` with `memberId` in form data
- `POST /api/skill/ocr` with `{ "memberId": "xxx" }`

## Recommended Workflow

When a user asks "show my wife's blood sugar":
1. `GET /api/skill/members` — find the spouse member
2. `GET /api/skill/indicators?memberId={spouse_id}` — find blood sugar indicator
3. `GET /api/skill/indicators/trend?id={indicator_uuid}` — get trend

When a user asks "upload this report for my child":
1. `GET /api/skill/members` — find the child member
2. `POST /api/skill/upload` with `memberId={child_id}`
3. `POST /api/skill/ocr` with `memberId={child_id}`

## Notes

- Every account has a default member (the user themselves, `is_default: 1`)
- If no `memberId` is specified, queries return data for the default member
- The `relationship` field indicates: self, spouse, child, parent, sibling, other
