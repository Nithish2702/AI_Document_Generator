# AI Document Generator - Frontend

React + TypeScript frontend for the AI-powered document generation system.

## Features

- **Document Generation Form**: Intuitive interface for requesting document generation
- **Document Library**: View and manage all generated documents
- **Real-time Status**: Track document generation progress
- **Download**: Download generated documents in PDF or DOCX format
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **State Management**: TanStack Query (React Query)
- **Forms**: React Hook Form
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env`:
```
VITE_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### 4. Build for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts           # Axios client configuration
│   │   └── documentService.ts  # API service functions
│   ├── components/
│   │   └── layout/
│       └── Layout.tsx          # Main layout component
│   ├── pages/
│   │   ├── DocumentRequestPage.tsx   # Document generation form
│   │   ├── DocumentListPage.tsx      # Document library
│   │   └── DocumentViewPage.tsx      # Document details & download
│   ├── types/
│   │   └── index.ts            # TypeScript type definitions
│   ├── App.tsx                 # Main app component
│   ├── main.tsx                # Entry point
│   └── index.css               # Global styles
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Usage

### Generate a Document

1. Navigate to the home page
2. Select document type (proposal, report, memo, etc.)
3. Enter document title and description
4. Provide additional context (optional)
5. Choose tone, length, and output format
6. Click "Generate Document"
7. Wait for generation to complete (30-60 seconds)
8. Download your document

### View Documents

1. Click "My Documents" in the navigation
2. Browse your generated documents
3. Click on a document to view details
4. Download or delete documents

## API Integration

The frontend communicates with the backend API at `http://localhost:8000` (configurable via `VITE_API_URL`).

### Key Endpoints Used

- `POST /api/documents/generate` - Generate new document
- `GET /api/documents/generated/list` - List generated documents
- `GET /api/documents/generated/{id}` - Get document details
- `GET /api/documents/generated/{id}/download` - Download document
- `DELETE /api/documents/generated/{id}` - Delete document

## Styling

The app uses Tailwind CSS for styling. Key design principles:

- **Clean & Modern**: Minimalist interface focused on usability
- **Responsive**: Mobile-first design that works on all screen sizes
- **Accessible**: Proper contrast ratios and semantic HTML
- **Consistent**: Unified color scheme and spacing

## State Management

Uses TanStack Query (React Query) for:
- Server state management
- Caching
- Automatic refetching
- Loading and error states

## Form Handling

Uses React Hook Form for:
- Form validation
- Error handling
- Type-safe form data

## Development Tips

### Hot Module Replacement

Vite provides fast HMR. Changes to components will reflect immediately without full page reload.

### TypeScript

All components are written in TypeScript for type safety. Run `npm run build` to check for type errors.

### Linting

Run `npm run lint` to check for code quality issues.

## Deployment

### Build

```bash
npm run build
```

### Deploy to Static Hosting

The `dist/` folder can be deployed to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages
- Any static hosting service

### Environment Variables

Set `VITE_API_URL` to your production API URL.

## Troubleshooting

### API Connection Issues

- Ensure backend is running at the configured `VITE_API_URL`
- Check CORS settings in backend
- Verify network connectivity

### Build Errors

- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`

## License

MIT
