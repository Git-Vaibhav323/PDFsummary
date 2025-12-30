# PDF Intelligence Assistant - Frontend

Modern, enterprise-grade React frontend for the PDF chatbot application.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui (Radix-based)
- **Icons:** lucide-react
- **HTTP Client:** Axios

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Install shadcn/ui Components

```bash
npx shadcn@latest init
```

When prompted:
- TypeScript: Yes
- Style: Default
- Base color: Slate
- CSS file: `app/globals.css`
- Use CSS variables: Yes
- Tailwind config: `tailwind.config.ts`
- Component alias: `@/components`
- Utils alias: `@/lib/utils`
- React Server Components: Yes

### 3. Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Project Structure

```
frontend/
├── app/
│   ├── globals.css          # Global styles
│   ├── layout.tsx           # Root layout
│   └── page.tsx             # Main page
├── components/
│   ├── ui/                  # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   └── badge.tsx
│   ├── TopNavbar.tsx        # Top navigation
│   ├── Sidebar.tsx          # Left sidebar
│   ├── UploadCard.tsx       # PDF upload component
│   ├── StatusBadge.tsx      # Status indicator
│   ├── ChatWindow.tsx       # Chat messages container
│   ├── ChatMessage.tsx      # Individual message
│   ├── ChatInput.tsx        # Message input
│   ├── LoadingIndicator.tsx # Loading state
│   └── EmptyState.tsx       # Empty state
├── lib/
│   ├── api.ts               # API client
│   └── utils.ts             # Utility functions
└── hooks/
    └── use-toast.ts         # Toast notifications
```

## Features

- ✅ Modern, enterprise-grade UI
- ✅ Dark mode (default)
- ✅ Responsive design
- ✅ Drag & drop file upload
- ✅ Real-time chat interface
- ✅ Chart visualization support
- ✅ Loading states and error handling
- ✅ Smooth animations
- ✅ Professional typography and spacing

## Backend Integration

The frontend connects to the FastAPI backend at `http://localhost:8000` by default.

**Endpoints:**
- `POST /upload_pdf` - Upload PDF file
- `POST /chat` - Send chat message
- `GET /health` - Health check

Make sure the backend is running before starting the frontend.

