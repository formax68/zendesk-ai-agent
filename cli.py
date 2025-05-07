import argparse
import json
import os
import gradio as gr
from zendesk_client import ZendeskClient
from model_provider import ModelProvider

def setup_cli():
    """Set up and return the argument parser for the CLI"""
    parser = argparse.ArgumentParser(description="Zendesk CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Tickets command
    tickets_parser = subparsers.add_parser('tickets', help='List tickets')
    tickets_parser.add_argument('--status', help='Filter tickets by status')

    # Comments command
    comments_parser = subparsers.add_parser('comments', help='Show comments for a ticket')
    comments_parser.add_argument('ticket_id', type=int, help='Ticket ID to fetch comments for')

    # Summarize command
    summarize_parser = subparsers.add_parser('summarize', help='Summarize comments for a ticket')
    summarize_parser.add_argument('ticket_id', type=int, help='Ticket ID to summarize comments for')
    summarize_parser.add_argument('--provider', choices=['ollama', 'openai'], default='ollama', 
                                help='AI provider to use (default: ollama)')
    summarize_parser.add_argument('--model', help='Model to use (default: llama3.2 for ollama, gpt-4o-mini for openai)')

    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Chat with the model')
    chat_parser.add_argument('--provider', choices=['ollama', 'openai'], default='ollama', 
                           help='AI provider to use (default: ollama)')
    chat_parser.add_argument('--model', help='Model to use (default: llama3.2 for ollama, gpt-4o-mini for openai)')

    return parser

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
    model_provider = ModelProvider(provider, model)
    return model_provider.generate_response(prompt, system_prompt)

def execute_command(args):
    """Execute the command specified by the parsed arguments"""
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
    
    elif args.command == 'chat':
        # Load system prompt for role guidance
        with open(os.path.join(os.path.dirname(__file__), "system_prompt.txt"), 'r') as f:
            system_prompt = f.read()
        
        # Initialize model provider
        model_provider = ModelProvider(args.provider, args.model)
        
        # Define a chat function that converts the generator to a string
        def chat_fn(message, history):
            # Convert gradio history format to the format expected by model_provider
            # Gradio history is a list of [user_message, assistant_response] pairs
            model_history = []
            for user_msg, assistant_msg in history:
                model_history.append({"role": "user", "content": user_msg})
                model_history.append({"role": "assistant", "content": assistant_msg})
            
            # Convert generator to final string result
            response_generator = model_provider.chat(message, system_prompt, model_history)
            final_response = ""
            for response in response_generator:
                final_response = response  # Will get the last yielded value
            
            return final_response
        
        # Launch Gradio chat interface
        print("Starting chat interface")
        gr.ChatInterface(
            fn=chat_fn,
            title="Zendesk Agent - Chat",
            description="Chat with the AI assistant"
        ).launch()