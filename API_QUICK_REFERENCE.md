# API Quick Reference

## Endpoints

### Activities List
```
GET /api/activities
```

**Params:**
- `since` - Activities from this date (e.g., `2024-01-01`)
- `sportType` - Filter by sport (Run, Ride, Swim, etc.)
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 50, max: 100)

**Response:** Array of activities with pagination metadata

---

### Monthly Statistics
```
GET /api/stats/monthly
```

**Params:**
- `year` - Specific year (e.g., `2024`)
- `sportType` - Filter by sport (Run, Ride, etc.)

**Response:** Monthly breakdown with summary totals

## Example cURL Commands

```bash
# All activities
curl http://localhost:8000/api/activities

# Run activities since Jan 2024
curl http://localhost:8000/api/activities?sportType=Run&since=2024-01-01

# Page 2 of Ride activities
curl http://localhost:8000/api/activities?sportType=Ride&page=2&limit=20

# 2024 monthly stats
curl http://localhost:8000/api/stats/monthly?year=2024

# Run stats for 2024
curl http://localhost:8000/api/stats/monthly?year=2024&sportType=Run

# All monthly stats
curl http://localhost:8000/api/stats/monthly
```

## Response Examples

### /api/activities
```json
{
  "data": [
    {
      "id": "123",
      "name": "Morning Run",
      "sportType": "Run",
      "activityType": "Running",
      "distance": 5.2,
      "movingTime": 1800,
      "totalElevationGain": 45,
      "averageSpeed": 10.4,
      "averageHeartRate": 145,
      "startDate": "2024-03-15T10:30:00Z",
      "kudosCount": 5,
      "isCommute": false
    }
  ],
  "pagination": {
    "total": 250,
    "page": 1,
    "limit": 50,
    "totalPages": 5,
    "hasNextPage": true,
    "hasPreviousPage": false
  }
}
```

### /api/stats/monthly
```json
{
  "data": [
    {
      "month": "2024-03",
      "monthsAgo": 0,
      "sportTypes": [
        {
          "sportType": "Run",
          "numberOfActivities": 15,
          "distance": 150.5,
          "movingTime": 45000
        }
      ],
      "totals": {
        "numberOfActivities": 15,
        "distance": 150.5,
        "movingTime": 45000
      }
    }
  ],
  "summary": {
    "numberOfActivities": 250,
    "distance": 5200.5,
    "movingTime": 850000
  }
}
```

## Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found

## Notes

- All endpoints are GET-only (read-only)
- No authentication required
- Default page size: 50 items
- Maximum page size: 100 items
- Sport types: Run, Ride, Swim, Walk, Hike, Workout, Yoga, etc. (50+ supported)