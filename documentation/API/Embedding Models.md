QueryLake supports the deployment of local embedding models, such as `bge-m3`.

You can call an embedding model like so:
```python
input.update({
	"auth": {"api_key": "sk-123456789"},
    "inputs": ["Test text 1", "Test text 2", "Test text 3"]
})
    
response = requests.get(f"http://localhost:8000/api/embedding", json=input)
response.raise_for_status()
```

### Result
```json
{ 
	"success": true,
	"result": [
		// Example embedding values
		[1, 2, 3, ...],
		[1, 2, 3, ...]
	]
}
```