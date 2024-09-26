QueryLake supports the deployment of re-rank models, such as `bge-reranker-v2`.
These are (typically) transformer models that take a pair of strings, a question and an answer, and score to how relevant the answer was to the question.

By default, QueryLake caps the returned float at 100 using a sigmoid function.

You can call these models like so:
```python
import requests

response = requests.get(f"http://localhost:8000/api/embedding", json={
	"auth": {"api_key": "sk-123456789"},
    "inputs": [
		[
			"What is the square root of 169?", 
			"The square root of 169 is 13."
		],
		[
			"What is the derivative of sin(cos(x))?", 
			"What is the derivative of sin(cos(x))? Well, it's a bit complicated. The derivative of sin(cos(x)) is cos(cos(x)) * -sin(x)."
		],
		[
			"What is the square root of 169?", 
			"cupcake"
		],
	]
})
result = response.raise_for_status().json()
```

### Result
```json
{
	'success': True, 
	'result': [
		100.0, 
		100.0,
		1.0827401638380252e-05
	]
}
```