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
        with open(os.path.join(os.path.dirname(__file__), "../config/system_prompt.txt"), 'r') as f:
            system_prompt = f.read()
        
        provider = args.provider
        model = args.model
        
        summary = generate_response(prompt, system_prompt, provider, model)
        print(summary)
    
    elif args.command == 'chat':
        # Load system prompt for role guidance
        with open(os.path.join(os.path.dirname(__file__), "../config/system_prompt.txt"), 'r') as f:
            system_prompt = f.read()
        
        # Initialize model provider
        model_provider = ModelProvider(args.provider, args.model)
        
        # Define function to handle chat interactions
        def user_message(message, history):
            # Add user message to history
            history.append({"role": "user", "content": message})
            return "", history
        
        # Define a function that streams the response
        def bot_message(history):
            # Get the last user message
            user_msg = history[-1]["content"]
            # Remove the last user message from history for generating response
            response_history = history[:-1]
            
            # Create assistant response placeholder
            history.append({"role": "assistant", "content": ""})
            last_reasoning = None
            last_content = ""
            # Generate streaming response
            for resp in model_provider.chat(user_msg, system_prompt, response_history):
                # resp is a dict: {"reasoning_content": ..., "content": ...} or {"content": ...}
                reasoning = resp.get("reasoning_content")
                content = resp.get("content", "")
                last_content = content
                # Compose display: show reasoning (if present) above answer
                if reasoning:
                    display = f"<div style='color: #888'><b>Thinking:</b><br>{reasoning}</div>\n---\n{content}"
                else:
                    display = content
                history[-1]["content"] = display
                yield history
        
        # Launch Gradio blocks interface
        print("Starting chat interface")
        with gr.Blocks(title="Zendesk Agent - Chat") as demo:
            gr.Markdown("# Zendesk Agent - Chat")
            gr.Markdown("Chat with the Zendesk AI assistant")
            
            # Create chatbot component
            chatbot = gr.Chatbot(type="messages")
            
            # Create message input
            msg = gr.Textbox(placeholder="Type your message here...", scale=4)
            
            # Create clear button
            clear = gr.ClearButton([msg, chatbot])
            
            # Set up event handlers
            msg.submit(
                user_message, 
                [msg, chatbot], 
                [msg, chatbot]
            ).then(
                bot_message,
                chatbot,
                chatbot
            )
            
        demo.launch()