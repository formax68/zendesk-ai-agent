# Zendesk AI Agent

A simple Python project to interact with the Zendesk and use AI to summarize ticket comments and suggest next actions.

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Copy the example environment file and fill in your credentials:

   ```bash
   cp .env.example .env
   ```

3. Open `.env` and set:

   ```dotenv
   ZENDESK_SUBDOMAIN=your_subdomain
   ZENDESK_EMAIL=your_email
   ZENDESK_API_TOKEN=your_api_token
   OPENAI_API_KEY=your_openai_api_key  # Required only if using OpenAI as provider
   OLLAMA_URL=http://localhost:11434   # Optional: URL for Ollama API (defaults to localhost:11434)
   ```

## Usage

Run the CLI:

```bash
python main.py tickets [--status STATUS]
python main.py comments TICKET_ID
python main.py summarize TICKET_ID [--provider {ollama|openai}] [--model MODEL_NAME]
python main.py chat [--provider {ollama|openai}] [--model MODEL_NAME]
```

Examples:

```bash
# List all open tickets
python main.py tickets --status open

# Fetch comments for ticket #123
python main.py comments 123

# Summarize comments for ticket #123 (default: uses Ollama with llama3.2)
python main.py summarize 123

# Summarize using Ollama with a specific model
python main.py summarize 123 --model llama3

# Summarize using OpenAI
python main.py summarize 123 --provider openai

# Summarize using OpenAI with a specific model
python main.py summarize 123 --provider openai --model gpt-4

# Chat with the LLM (default: uses Ollama with llama3.2)
python main.py chat
```

## AI Provider Options

The Zendesk AI Agent supports multiple AI provider options:

### Ollama (Default)

By default, the application uses Ollama with the `llama3.2` model, which provides local inference without requiring external API calls. This is ideal for:

- Maintaining data privacy by keeping all processing local
- Eliminating API costs
- Working in environments with limited or no internet connectivity

### OpenAI

For cases where you need increased capability, you can use OpenAI's models:

- Higher accuracy for complex summarization tasks
- Better handling of nuanced customer sentiment
- Access to more powerful models like GPT-4

## System Prompt

The Zendesk AI Agent uses a customizable system prompt that guides the AI model in generating relevant and useful ticket summaries. The prompt is stored in `system_prompt.txt` and can be modified to better suit your specific support needs.

The default system prompt instructs the AI to:

- Extract key issues from ticket comments
- Identify customer sentiment
- Highlight action items for support agents
- Format the output in a concise, structured way

### Customizing the System Prompt

You can edit the `system_prompt.txt` file to customize how the AI processes and summarizes ticket comments. Some examples of custom prompts:

1. **Technical Support Focus**:

   ```plaintext
   You are an expert technical support assistant. Analyze these Zendesk ticket comments and:
   1. Identify the core technical issue
   2. List troubleshooting steps already attempted
   3. Suggest next technical steps for resolution
   4. Highlight any system requirements or compatibility issues mentioned
   ```

2. **Customer Sentiment Analysis**:

   ```plaintext
   You are a customer satisfaction analyst. Review these Zendesk comments and:
   1. Rate the customer's satisfaction level (1-5)
   2. Extract specific pain points mentioned
   3. Identify opportunities to improve customer experience
   4. Note any positive feedback or compliments
   ```

3. **Action-Oriented Summary**:

   ```plaintext
   You are a support team coordinator. Analyze these ticket comments and create:
   1. A prioritized list of action items for the support team
   2. Required resources or expertise needed
   3. Estimated resolution complexity (Low/Medium/High)
   4. Recommended follow-up timeline
   ```

## Cost-Efficient AI Processing

This tool uses the **4o-mini model** from OpenAI for ticket summarization, providing an excellent balance between performance and cost. This model was specifically chosen to:

- Keep API usage costs low while maintaining high-quality summaries
- Enable processing of more tickets within budget constraints
- Reduce response latency compared to larger models

The 4o-mini model is particularly effective for support ticket summarization tasks while costing significantly less than larger models like GPT-4.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
