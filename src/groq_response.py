from groq import Groq
import os

def GroqResponse(user_prompt: str,system_prompt="you are a helpful assistant"):
    """Generate a response using Groq's chat completion API with Llama 4 Scout model."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
            "role": "system",
            "content": system_prompt
            },
            {
            "role": "user",
            "content": user_prompt
            }
        ],
        max_completion_tokens=1024,
        stream=False,
        stop=None,
    )

    return completion.choices[0].message.content

if __name__ == "__main__":
    # Example usage
    prompt = "What is the capital of France?"
    response = GroqResponse(prompt)
    print(response)  # Should print "The capital of France is Paris."