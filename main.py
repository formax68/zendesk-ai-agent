import argparse
import json
import openai
import os
from dotenv import load_dotenv
from zendesk_client import ZendeskClient

load_dotenv()  # load OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")


def main():
    parser = argparse.ArgumentParser(description="Zendesk CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)

    tickets_parser = subparsers.add_parser('tickets', help='List tickets')
    tickets_parser.add_argument('--status', help='Filter tickets by status')

    comments_parser = subparsers.add_parser('comments', help='Show comments for a ticket')
    comments_parser.add_argument('ticket_id', type=int, help='Ticket ID to fetch comments for')

    summarize_parser = subparsers.add_parser('summarize', help='Summarize comments for a ticket')
    summarize_parser.add_argument('ticket_id', type=int, help='Ticket ID to summarize comments for')

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
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        summary = response.choices[0].message.content.strip()
        print(summary)


if __name__ == '__main__':
    main()
