# The Core Flow - AI Decision Tree

An AI-powered decision tree that helps you explore the consequences of your choices through a 3-round guided journey.

## Features

- **Contextual AI Choices**: Claude generates meaningful, distinct options based on your question and prior choices
- **3-Round Decision Path**: Navigate through progressively deeper choices
- **Visual Path Tracking**: Live breadcrumb trail showing your full decision journey
- **Animated Progress**: Progress dots that animate as you advance
- **Final Insight**: Personalized outcome summary based on your unique path
- **Beautiful UI**: Clean serif/mono typography with thoughtful animations

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure API Key

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Then edit `.env` and add your Anthropic API key:

```
VITE_ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
```

**Get your API key**: Visit [console.anthropic.com](https://console.anthropic.com/) to create an account and generate an API key.

### 3. Run the Development Server

```bash
npm run dev
```

Open your browser to the URL shown (typically `http://localhost:5173`)

## Usage

1. Enter any question or dilemma you're facing
2. Choose between two AI-generated options
3. Continue for 3 rounds, with each choice influencing the next
4. Receive a personalized insight about where your path leads
5. Start a new decision tree anytime

## Build for Production

```bash
npm run build
npm run preview
```

## Tech Stack

- **React** - UI framework
- **Vite** - Build tool and dev server
- **Claude Sonnet 4** - AI model for generating choices and insights
- **Anthropic API** - Direct API integration

## Important Note

⚠️ **Security Warning**: This app makes API calls directly from the browser, which exposes your API key in the client code. This is fine for local development and personal use, but **NOT suitable for production deployment**.

For production, you should:
- Move API calls to a backend server
- Use environment variables on the server side
- Implement rate limiting and authentication

## License

MIT
