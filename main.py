import argparse
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from zendesk_client import ZendeskClient

load_dotenv()  # load environment variables

def generate_response(prompt, system_prompt, provider="ollama", model=None):
    """Generate response using either OpenAI or Ollama API
    
    Args:
        prompt (str): The user prompt
        system_prompt (str): The system instructions
        provider (str): 'openai' or 'ollama'
        model (str): Model to use, defaults to provider-specific model if None
    
    Returns:
        str: The generated response
    """
    # Set default models based on provider
    if model is None:
        model = "gpt-4o-mini" if provider == "openai" else "llama3.2"
    
    # Configure client based on provider
    if provider == "openai":
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    else:  # ollama
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        client = OpenAI(
            base_url=f"{ollama_url}/v1",
            api_key="ollama",  # Ollama doesn't need an API key, but the client requires one
        )
    
    # Try to generate the response
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Only try the fallback for Ollama
        if provider != "openai":
            # Fall back to alternative Ollama API format if needed
            client = OpenAI(
                base_url=f"{ollama_url}/api",
                api_key="ollama",
            )
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        else:
            # Re-raise the exception for OpenAI errors
            raise


def main():
    parser = argparse.ArgumentParser(description="Zendesk CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)

    tickets_parser = subparsers.add_parser('tickets', help='List tickets')
    tickets_parser.add_argument('--status', help='Filter tickets by status')

    comments_parser = subparsers.add_parser('comments', help='Show comments for a ticket')
    comments_parser.add_argument('ticket_id', type=int, help='Ticket ID to fetch comments for')

    # Update summarize parser with provider and model parameters
    summarize_parser = subparsers.add_parser('summarize', help='Summarize comments for a ticket')
    summarize_parser.add_argument('ticket_id', type=int, help='Ticket ID to summarize comments for')
    summarize_parser.add_argument('--provider', choices=['ollama', 'openai'], default='ollama', 
                               help='AI provider to use (default: ollama)')
    summarize_parser.add_argument('--model', help='Model to use (default: llama3.2 for ollama, gpt-4o-mini for openai)')

    args = parser.parse_args()

    client = ZendeskClient()

    if args.command == 'tickets':
        tickets = client.get_tickets(status=args.status)
        print(json.dumps(tickets, indent=2))
    elif args.command == 'comments':
        comments = client.get_ticket_comments(args.ticket_id)
        print(json.dumps(comments, indent=2))
    elif args.command == 'summarize':
        comments = client.get_ticket_comments(args.ticket_id)
        bodies = [c.get('body', '') for c in comments]
        prompt = "Summarize the following ticket comments:\n" + "\n".join(bodies)
        
        # Load system prompt for role guidance
        with open(os.path.join(os.path.dirname(__file__), "system_prompt.txt"), 'r') as f:
            system_prompt = f.read()
        
        provider = args.provider
        model = args.model
        
        summary = generate_response(prompt, system_prompt, provider, model)
        print(summary)


if __name__ == '__main__':
    main()
