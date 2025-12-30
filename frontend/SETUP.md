# Frontend Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Install shadcn/ui

```bash
npx shadcn@latest init
```

**Configuration:**
- TypeScript: Yes
- Style: Default
- Base color: Slate
- CSS file: `app/globals.css`
- Use CSS variables: Yes
- Tailwind config: `tailwind.config.ts`
- Component alias: `@/components`
- Utils alias: `@/lib/utils`
- React Server Components: Yes

### 3. Environment Setup

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Run Development Server

```bash
npm run dev
```

Visit: `http://localhost:3000`

## Project Structure

```
frontend/
├── app/
│   ├── globals.css       # Global styles & Tailwind
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Main application page
├── components/
│   ├── ui/               # shadcn/ui base components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   └── badge.tsx
│   ├── TopNavbar.tsx     # Top navigation bar
│   ├── Sidebar.tsx       # Left sidebar with upload
│   ├── UploadCard.tsx   # PDF upload component
│   ├── StatusBadge.tsx  # Status indicator
│   ├── ChatWindow.tsx   # Chat messages container
│   ├── ChatMessage.tsx # Individual message component
│   ├── ChatInput.tsx    # Message input field
│   ├── LoadingIndicator.tsx
│   └── EmptyState.tsx   # Empty state screens
├── lib/
│   ├── api.ts           # API client (Axios)
│   └── utils.ts         # Utility functions
└── hooks/
    └── use-toast.ts     # Toast notifications
```

## Features Implemented

✅ **Modern Enterprise UI**
- Clean, professional design
- Dark mode (default)
- Responsive layout
- Smooth animations

✅ **PDF Upload**
- Drag & drop support
- File browser
- Upload progress
- File preview

✅ **Chat Interface**
- Real-time messaging
- Message history
- Chart visualization support
- Loading states
- Error handling

✅ **UX Polish**
- Empty states
- Loading indicators
- Status badges
- Smooth scrolling
- Keyboard shortcuts (Enter to send)

## Backend Integration

The frontend connects to your FastAPI backend:

- **Upload:** `POST /upload_pdf`
- **Chat:** `POST /chat`
- **Health:** `GET /health`

Make sure your backend is running on `http://localhost:8000` (or update `.env.local`).

## Troubleshooting

### TypeScript Errors

If you see TypeScript errors about missing types:

```bash
npm install --save-dev @types/react @types/react-dom
```

### shadcn/ui Not Working

Make sure you've run `npx shadcn@latest init` and all components are in `components/ui/`.

### API Connection Issues

1. Verify backend is running: `python run.py`
2. Check CORS is enabled in backend
3. Verify `NEXT_PUBLIC_API_URL` in `.env.local`

### Build Issues

```bash
rm -rf .next node_modules
npm install
npm run dev
```

## Production Build

```bash
npm run build
npm start
```

The production build will be in the `.next` folder.

