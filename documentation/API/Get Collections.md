# fetch_document_collections_belonging_to API Documentation

## Overview
The `fetch_document_collections_belonging_to` endpoint retrieves a list of document collections for a user. If an `organization_id` is provided, the user must be an accepted member of that organization to access the collections. If `organization_id` is not provided, the endpoint will return the user's personal collections.

## Endpoint
```
GET /api/fetch_document_collections_belonging_to
```

## Authentication
This endpoint supports authentication through the following methods:
- **API Key** (preferred method for accessing this endpoint)
- **OAuth2**
- **Username and Password**

Note: Authentication can only be done using one method at a time.

## Parameters
| Parameter            | Type   | Default | Description                                                                                   |
|----------------------|--------|---------|-----------------------------------------------------------------------------------------------|
| `auth`               | object | N/A     | Authentication info (API Key, OAuth2, or username/password).                               |
| `organization_id`    | int    | None    | The ID of the organization whose collections are to be fetched. If None, personal collections are retrieved. |
| `global_collections` | bool   | False   | Flag to indicate whether to retrieve global collections.                                      |

## Response Structure
The API will return a JSON object containing the following keys:
- `success`: A boolean indicating the success of the operation.
- `result`: An object containing the retrieved collections.

### Example Response
```json
{
    "success": true,
    "result": {
        "collections": []
    }
}
```

## Usage Example

### Python
```python
import requests, json

input_data = {
    "auth": {"api_key": "example_api_key"},
    "organization_id": None,
    "global_collections": False
}

response = requests.get("http://localhost:8000/api/fetch_document_collections_belonging_to", json=input_data)
result = response.json()

print(json.dumps(result, indent=4))
```

### JavaScript
```javascript
const inputData = {
    auth: { api_key: "example_api_key" },
    organization_id: null,
    global_collections: false
};

fetch("http://localhost:8000/api/fetch_document_collections_belonging_to", {
    method: "GET",
    body: JSON.stringify(inputData),
    headers: {
        "Content-Type": "application/json"
    }
})
.then(response => response.json())
.then(result => console.log(JSON.stringify(result, null, 4)));
```

---

Use this documentation as a guide to integrate with the `fetch_document_collections_belonging_to` API endpoint. For any requests requiring different authentication methods, refer to the general structure described above.