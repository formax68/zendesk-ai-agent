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
            str: Incrementally generated response text
        """
        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model, 
                messages=messages, 
                stream=True
            )

            response = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    response += chunk.choices[0].delta.content
                    yield response
                    
        except Exception as e:
            # Only try the fallback for Ollama
            if self.provider != "openai":
                try:
                    # Fall back to alternative Ollama API format
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
                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content is not None:
                            response += chunk.choices[0].delta.content
                            yield response
                            
                except Exception as fallback_error:
                    # If fallback also fails, yield error message
                    yield f"Error generating response: {str(fallback_error)}"
            else:
                # For OpenAI, yield the error message
                yield f"Error generating response: {str(e)}"

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