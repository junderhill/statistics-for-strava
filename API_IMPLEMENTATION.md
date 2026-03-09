# Statistics for Strava API Implementation

## Overview

This document describes the REST API implementation for Statistics for Strava, enabling programmatic access to activity data and statistics.

## Implementation Status

✅ **Complete** - All Phase 1 endpoints have been implemented and are ready for use.

## API Endpoints

### 1. Activities List

**Endpoint:** `GET /api/activities`

**Description:** Retrieve a paginated list of activities with optional filtering.

**Query Parameters:**
- `since` (optional) - Filter activities from this date onwards (e.g., `2024-01-01`, `2024-01-01T00:00:00Z`)
- `sportType` (optional) - Filter by sport type (e.g., `Run`, `Ride`, `Swim`, `Walk`, `Hike`, etc.)
- `page` (optional) - Page number (default: 1, minimum: 1)
- `limit` (optional) - Items per page (default: 50, range: 1-100)

**Response Format:**
```json
{
  "data": [
    {
      "id": "activity-id",
      "name": "Activity Name",
      "sportType": "Run",
      "activityType": "Running",
      "distance": 10.5,
      "movingTime": 3600,
      "totalElevationGain": 150,
      "averageSpeed": 10.5,
      "maxSpeed": 15.2,
      "averageHeartRate": 145,
      "maxHeartRate": 165,
      "averagePower": null,
      "maxPower": null,
      "startDate": "2024-03-15T10:30:00Z",
      "kudosCount": 12,
      "isCommute": false,
      "deviceName": "Garmin Forerunner 945"
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

**Example Requests:**
```bash
# Get all activities (paginated)
curl "http://localhost:8000/api/activities"

# Get activities since a specific date
curl "http://localhost:8000/api/activities?since=2024-01-01"

# Get only Run activities, page 2
curl "http://localhost:8000/api/activities?sportType=Run&page=2"

# Get Ride activities since Jan 2024, 20 per page
curl "http://localhost:8000/api/activities?sportType=Ride&since=2024-01-01&limit=20"
```

### 2. Monthly Statistics

**Endpoint:** `GET /api/stats/monthly`

**Description:** Retrieve aggregated monthly statistics with optional filtering.

**Query Parameters:**
- `year` (optional) - Filter by specific year (4-digit year, e.g., `2024`)
- `sportType` (optional) - Filter by sport type (e.g., `Run`, `Ride`, etc.)

**Response Format:**
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
          "elevation": 1200,
          "movingTime": 45000,
          "calories": 9000
        },
        {
          "sportType": "Ride",
          "numberOfActivities": 8,
          "distance": 320.0,
          "elevation": 2500,
          "movingTime": 48000,
          "calories": 8000
        }
      ],
      "totals": {
        "numberOfActivities": 23,
        "distance": 470.5,
        "elevation": 3700,
        "movingTime": 93000,
        "calories": 17000
      }
    }
  ],
  "summary": {
    "numberOfActivities": 250,
    "distance": 5200.5,
    "elevation": 45000,
    "movingTime": 850000,
    "calories": 180000
  }
}
```

**Example Requests:**
```bash
# Get all monthly stats
curl "http://localhost:8000/api/stats/monthly"

# Get stats for 2024 only
curl "http://localhost:8000/api/stats/monthly?year=2024"

# Get Run stats only
curl "http://localhost:8000/api/stats/monthly?sportType=Run"

# Get 2024 Ride stats
curl "http://localhost:8000/api/stats/monthly?year=2024&sportType=Ride"
```

## Implementation Details

### Modified Files

1. **src/Controller/ApiRequestHandler.php**
   - Added QueryBus dependency injection
   - Implemented dynamic route handling for `/api/activities` and `/api/stats/monthly`
   - Added query parameter validation
   - Added error handling for invalid parameters

2. **src/Domain/Activity/DbalActivityRepository.php**
   - Added `findAllWithFilters()` method with pagination support
   - Added `countWithFilters()` method for pagination metadata

3. **src/Domain/Calendar/FindMonthlyStats/FindMonthlyStats.php**
   - Added `$year` and `$sportType` parameters
   - Added getter methods for parameters

4. **src/Domain/Calendar/FindMonthlyStats/FindMonthlyStatsQueryHandler.php**
   - Added WHERE clauses for year filtering
   - Added WHERE clauses for sport type filtering
   - Applied same filters to min/max date queries

### Created Files

5. **src/Domain/Activity/Api/FindActivities.php**
   - Query object for activities list with filters and pagination parameters

6. **src/Domain/Activity/Api/FindActivitiesQueryHandler.php**
   - Query handler following CQRS pattern
   - Uses repository methods and returns ActivitiesResponse

7. **src/Infrastructure/Http/Api/ActivitiesResponse.php**
   - Response formatter for activities list
   - Includes pagination metadata
   - Formats activity data consistently

8. **src/Infrastructure/Http/Api/MonthlyStatsResponse.php**
   - Response formatter for monthly statistics
   - Groups data by month
   - Includes summary totals

## Architecture

### Design Patterns

- **CQRS (Command Query Responsibility Segregation):** Queries are handled by dedicated query handlers
- **DDD (Domain-Driven Design):** Domain entities and value objects are used throughout
- **Repository Pattern:** Data access is abstracted through repositories

### Key Components

- **Query Bus:** Dispatches queries to appropriate handlers
- **Repositories:** Handle data access and persistence
- **Response Formatters:** Format query results into JSON responses
- **Value Objects:** Strong typing for domain concepts (SportType, etc.)

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- **400 Bad Request:** Invalid query parameters
- **404 Not Found:** Static API files that don't exist (legacy support)

**Error Response Format:**
```json
{
  "error": "Error message describing the issue"
}
```

## Pagination

- Default limit: 50 items per page
- Maximum limit: 100 items per page
- Metadata includes: total count, current page, total pages, hasNextPage, hasPreviousPage

## Authentication

Currently, **no authentication is required**. The API provides public access to the data. This is suitable for personal self-hosted instances but should be reviewed if exposing the API publicly.

## Performance Considerations

- Database queries use indexes on `startDateTime` and `sportType` columns
- Pagination uses LIMIT/OFFSET for efficient data retrieval
- SQL aggregation functions are used for monthly statistics

## Testing

### Test Coverage

Unit tests should be created for:
- Repository filtering methods with various parameters
- Query handlers with mock data
- Response formatters
- ApiRequestHandler route dispatching

### Manual Testing

To test the API manually:

1. Start the application server
2. Use curl or a REST client to make requests
3. Verify responses match expected format
4. Test pagination by requesting different pages
5. Test filtering with various sport types and dates

## Future Enhancements (Phase 2)

Potential future API endpoints:

- `GET /api/activities/{id}` - Individual activity details
- `GET /api/stats/yearly` - Yearly statistics
- `GET /api/gear/stats` - Gear statistics
- `GET /api/challenges/progress` - Challenge progress
- `GET /api/activities/{id}/streams` - Activity time-series data
- `GET /api/best-efforts` - Personal records
- `GET /api/athlete/profile` - Athlete profile information

## Support

For issues or questions about the API implementation, please refer to the application documentation or create an issue in the project repository.