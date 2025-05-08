import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # load environment variables

class ModelProvider:
    """Class to handle AI model provider selection and response generation"""
    
    def __init__(self, provider="ollama", model=None):
        """Initialize the model provider
        
        Args:
            provider (str): 'openai' or 'ollama'
            model (str): Model to use, defaults to provider-specific model if None
        """
        self.provider = provider
        
        # Set default models based on provider
        if model is None:
            self.model = "gpt-4o-mini" if provider == "openai" else "llama3.2"
        else:
            self.model = model
        
        self._init_client()
    
    def _init_client(self):
        """Initialize the appropriate client based on provider"""
        if self.provider == "openai":
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:  # ollama
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            self.client = OpenAI(
                base_url=f"{ollama_url}/v1",
                api_key="ollama",  # Ollama doesn't need an API key, but the client requires one
            )
            self.ollama_url = ollama_url  # Store for potential fallback

    def chat(self, message, system_prompt, history):
        """Generate streaming response using the configured provider and model
        
        Args:
            message (str): The user message
            system_prompt (str): The system instructions
            history (list): Previous conversation history
            
        Yields:
            dict: {'reasoning_content': str or None, 'content': str}
        """
        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
        
        def is_qwen3():
            # crude check for Qwen3 model name
            return "qwen" in self.model.lower() or "qwen3" in self.model.lower()

        try:
            stream = self.client.chat.completions.create(
                model=self.model, 
                messages=messages, 
                stream=True
            )

            response = ""
            reasoning = ""
            for chunk in stream:
                # Qwen3 returns reasoning_content and content separately in delta
                delta = getattr(chunk.choices[0], "delta", None)
                if is_qwen3() and delta:
                    # Qwen3: delta may have reasoning_content and content
                    if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                        reasoning += delta.reasoning_content
                        yield {"reasoning_content": reasoning, "content": response}
                    if hasattr(delta, "content") and delta.content is not None:
                        response += delta.content
                        yield {"reasoning_content": reasoning if reasoning else None, "content": response}
                else:
                    # Other models: just content
                    if delta and getattr(delta, "content", None) is not None:
                        response += delta.content
                        yield {"content": response}
        
        except Exception as e:
            # Only try the fallback for Ollama
            if self.provider != "openai":
                try:
                    fallback_client = OpenAI(
                        base_url=f"{self.ollama_url}/api",
                        api_key="ollama",
                    )
                    stream = fallback_client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        stream=True
                    )
                    response = ""
                    reasoning = ""
                    for chunk in stream:
                        delta = getattr(chunk.choices[0], "delta", None)
                        if is_qwen3() and delta:
                            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                                reasoning += delta.reasoning_content
                                yield {"reasoning_content": reasoning, "content": response}
                            if hasattr(delta, "content") and delta.content is not None:
                                response += delta.content
                                yield {"reasoning_content": reasoning if reasoning else None, "content": response}
                        else:
                            if delta and getattr(delta, "content", None) is not None:
                                response += delta.content
                                yield {"content": response}
                except Exception as fallback_error:
                    yield {"content": f"Error generating response: {str(fallback_error)}"}
            else:
                yield {"content": f"Error generating response: {str(e)}"}

    def generate_response(self, prompt, system_prompt):
        """Generate response using the configured provider and model
        
        Args:
            prompt (str): The user prompt
            system_prompt (str): The system instructions
        
        Returns:
            str: The generated response
        """
        # Try to generate the response
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Only try the fallback for Ollama
            if self.provider != "openai":
                # Fall back to alternative Ollama API format if needed
                fallback_client = OpenAI(
                    base_url=f"{self.ollama_url}/api",
                    api_key="ollama",
                )
                
                response = fallback_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content.strip()
            else:
                # Re-raise the exception for OpenAI errors
                raise