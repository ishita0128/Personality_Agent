# Getting a Groq API Key

This project uses the Groq API to power the chatbot.

## Step 1: Create a Groq Account

Visit the Groq Console:

https://console.groq.com/

Sign up or log in with your account.

## Step 2: Generate an API Key

1. Open the Groq Console.
2. Navigate to **API Keys**.
3. Click **Create API Key**.
4. Copy the generated key and store it securely.

## Step 3: Create a `.env` File

In the project root directory, create a file named:

```text
.env
```

Add your API key:

```env
GROQ_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your actual Groq API key.

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 5: Run the Application

```bash
python app.py
```

## Security Notes

- Never commit your `.env` file to GitHub.
- Keep your API key private.
- Ensure `.env` is included in `.gitignore`.

Example `.gitignore`:

```text
.env
__pycache__/
*.pyc
venv/
```

## Example `.env.example`

You may include a template file in the repository:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Contributors should copy it to `.env` and add their own API key.
