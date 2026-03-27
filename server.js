import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

// Load .env.local file
dotenv.config({ path: '.env.local' });

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());

app.post('/api/anthropic', async (req, res) => {
  const API_KEY = process.env.ANTHROPIC_API_KEY;

  console.log('API Key present:', !!API_KEY);
  console.log('API Key starts with:', API_KEY ? API_KEY.substring(0, 15) + '...' : 'MISSING');

  if (!API_KEY) {
    return res.status(500).json({ error: 'API key not configured' });
  }

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle Anthropic API overload with a friendly message
      if (response.status === 529 || data.error?.type === 'overloaded_error') {
        return res.status(503).json({ 
          error: 'The AI service is temporarily overloaded. Please try again in a moment.' 
        });
      }
      return res.status(response.status).json(data);
    }

    return res.status(200).json(data);
  } catch (error) {
    console.error('Error calling Anthropic API:', error);
    return res.status(500).json({ error: 'Failed to call Anthropic API' });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 API server running on http://localhost:${PORT}`);
});
