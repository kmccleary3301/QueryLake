# API Documentation for `get_document_secure`

### ✅ `get_document_secure`

**Description**: Returns the document entry within the system database. Primarily used for internal calls.

**Endpoint**: `/api/get_document_secure`

**Authentication Methods**: 
- API Key
- OAuth2
- Username and Password

**Function Arguments**:
- `auth`: (required) Authentication method (one of the three methods mentioned).
- `hash_id`: (required) The unique identifier for the document.
- `return_document`: (optional) A boolean flag indicating whether to return the document content (default: `False`).

### Example Request

#### Python Example

```python
import requests, json

input = {
    "auth": {"api_key": "example_api_key"},
    "hash_id": "8JYLF6k9wpnkUbgZdOVowO2XhFXP1v5T",
    "return_document": False
}

response = requests.get("http://localhost:8000/api/get_document_secure", json=input)

result = response.json()
print(json.dumps(result, indent=4))
```

#### JavaScript Example

```javascript
const axios = require('axios');

const input = {
    auth: { api_key: "example_api_key" },
    hash_id: "8JYLF6k9wpnkUbgZdOVowO2XhFXP1v5T",
    return_document: false
};

axios.get("http://localhost:8000/api/get_document_secure", { data: input })
    .then(response => {
        console.log(JSON.stringify(response.data, null, 4));
    });
```

### Example Response

If the request is successful, the API will return a response in the following structure:

```json
{
    "success": true,
    "result": {
        "password": "95aca57fad431ef0a503a6d4ec6a9256f7055b4c1fac8a123aebe5423d1b2ce4",
        "hash_id": "8JYLF6k9wpnkUbgZdOVowO2XhFXP1v5T"
    }
}
```

### Notes
- Ensure that you replace `"example_api_key"` and `"hash_id"` with your actual API key and the document's hash ID you wish to retrieve.
- The `return_document` flag can be set to `True` if you want to receive the actual document in the response.