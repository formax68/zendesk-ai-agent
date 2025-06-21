import gradio as gr
system_prompt = """You are an expert technical support agent specializing in summarizing customer support tickets. Identify any missing information we might need to resolve the issue, and provide a concise summary of the ticket comments. If the ticket is already resolved, mention that in the summary.
    If you are unsure about something, please say so.
    Respond in Markdown format in this format:

    ## Summary

    ### Issue:

    {Brief description of the issue}

    ### Resolution:
    {Brief description of the resolution, if applicable}

    ### Missing Information:
    {List any missing information needed to resolve the issue, if applicable}

    ### Suggested reply {optional}:
    {If you identify a missing information, suggest a reply to the customer asking for that information. If no missing information is identified, do not include this section.}
    """

with gr.Blocks() as ui:

    def fetch_ticket(ticket_id):
        """Fetch ticket comments from Zendesk"""
        from zendesk_client import ZendeskClient
        client = ZendeskClient()
        comments = client.get_ticket_comments(ticket_id)
        return comments

    def summarize_with_status(ticket_id):
        """Wrapper function to handle status updates"""
        try:
            # Update status to show processing
            yield "🔄 Processing ticket...", ""
            
            # Call the main summarization function
            summary = summarize_ticket_internal(ticket_id)
            
            # Update status to show completion and return summary
            yield "✅ Summary complete!", summary
            
        except Exception as e:
            # Handle errors gracefully
            yield f"❌ Error: {str(e)}", "An error occurred while processing the ticket. Please try again."

    def summarize_ticket_internal(ticket_id):
        """Internal function to summarize ticket comments using the AI model"""
        from model_provider import ModelProvider
        from zendesk_client import ZendeskClient
        
        if not ticket_id or not ticket_id.strip():
            return "Please enter a valid ticket ID."
        
        client = ZendeskClient()
        comments = client.get_ticket_comments(ticket_id)
        
        if not comments:
            return "No comments found for this ticket."
        
        comments_string = '\n\n'.join([comment['body'] for comment in comments])
        prompt = comments_string
        
        model_provider = ModelProvider(provider="openai", model="o3-mini")
        summary = model_provider.generate_response(prompt, system_prompt=SYSTEM_PROMPT)
        
        return summary

    def summarize_ticket(ticket_id, progress=gr.Progress()):
        """Summarize ticket comments using the AI model with progress tracking"""
        from model_provider import ModelProvider
        from zendesk_client import ZendeskClient
        
        progress(0, desc="Starting ticket analysis...")
        
        if not ticket_id or not ticket_id.strip():
            return "Please enter a valid ticket ID."
        
        progress(0.2, desc="Connecting to Zendesk...")
        client = ZendeskClient()
        
        progress(0.4, desc="Fetching ticket comments...")
        comments = client.get_ticket_comments(ticket_id)
        
        if not comments:
            return "No comments found for this ticket."
        
        progress(0.6, desc="Processing comments...")
        comments_string = '\n\n'.join([comment['body'] for comment in comments])
        prompt = comments_string
        
        progress(0.8, desc="Generating AI summary...")
        model_provider = ModelProvider(provider="openai", model="o3-mini")
        summary = model_provider.generate_response(prompt, system_prompt=SYSTEM_PROMPT)
        
        progress(1.0, desc="Summary complete!")
        return summary

    with gr.Row():
        gr.Markdown("## Ticket Summarizer")
    with gr.Row():
        gr.Markdown("Summarizes Tickets. Please be mindful of the data you share, as it may contain sensitive information.")
    with gr.Row():
        ticket_number = gr.Textbox(label="Enter Ticket ID", placeholder="e.g., 12345")
    with gr.Row():
        btn_summarize = gr.Button("Summarize Ticket", variant="primary")
        status_indicator = gr.Markdown("Ready to summarize tickets", elem_id="status")
    with gr.Row():
        output_summary = gr.Markdown(label="Summary")

    btn_summarize.click(
        summarize_with_status, 
        inputs=ticket_number, 
        outputs=[status_indicator, output_summary]
    )


ui.launch(inbrowser=True)