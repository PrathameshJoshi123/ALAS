# ALAS Frontend

Modern, responsive frontend for the ALAS AI-powered legal contract analysis platform.

## Features

- 🔐 **Secure Authentication** - Login, signup with email verification
- 📄 **Contract Management** - Upload, view, and manage legal contracts
- 🤖 **AI Analysis** - View AI-generated risk assessments and clause analysis
- 📊 **Analytics Dashboard** - Track contract trends and risk metrics
- 🎨 **Modern UI** - Clean, professional interface with Tailwind CSS
- 📱 **Fully Responsive** - Works seamlessly on desktop, tablet, and mobile

## Tech Stack

- **Framework**: Next.js 14 (TypeScript)
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **UI Components**: Lucide Icons
- **Notifications**: React Hot Toast

## Getting Started

### Prerequisites

- Node.js 16+
- npm or yarn

### Installation

1. **Clone and navigate to frontend:**

```bash
cd frontend
```

2. **Install dependencies:**

```bash
npm install
# or
yarn install
```

3. **Set up environment variables:**

```bash
cp .env.example .env.local
```

Edit `.env.local` and update:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. **Run development server:**

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

## Project Structure

```
frontend/
├── app/
│   ├── auth/
│   │   ├── login/
│   │   ├── signup/
│   │   └── forgot-password/
│   ├── dashboard/
│   │   ├── contracts/
│   │   │   ├── [id]/
│   │   │   └── upload/
│   │   ├── analytics/
│   │   ├── settings/
│   │   └── layout.tsx
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   └── dashboard/
│       ├── Sidebar.tsx
│       └── Header.tsx
├── services/
│   └── api.ts
├── store/
│   └── authStore.ts
├── utils/
│   └── (utility functions)
├── package.json
├── next.config.js
├── tailwind.config.ts
└── tsconfig.json
```

## Pages & Routes

### Authentication Routes

- `/auth/login` - Login page
- `/auth/signup` - Sign up page
- `/auth/forgot-password` - Password recovery

### Dashboard Routes

- `/dashboard` - Overview dashboard
- `/dashboard/contracts` - Contract list
- `/dashboard/contracts/upload` - Upload contract
- `/dashboard/contracts/[id]` - Contract details & analysis
- `/dashboard/analytics` - Analytics & metrics
- `/dashboard/settings` - Account settings

## Key Components

### Layout Components

- **Sidebar** - Navigation menu with active route highlighting
- **Header** - User profile, notifications, logout

### Pages

- **Dashboard** - Overview with statistics and recent contracts
- **Contracts** - Full contract list with search and filters
- **Upload** - Drag-and-drop file upload with validation
- **Contract Details** - Risk analysis with expandable clauses
- **Analytics** - Performance metrics and trends
- **Settings** - Profile, security, and notification preferences

## API Integration

The frontend connects to the backend at:

```
API_URL: http://localhost:8000
```

### Authentication Flow

1. User signs up/logs in
2. Backend returns `access_token` and `refresh_token`
3. Tokens stored in localStorage and passed in Authorization header
4. Automatic token refresh on 401 responses

### Key API Endpoints

**Auth:**

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

**Contracts:**

- `POST /api/contracts/upload`
- `GET /api/contracts/list`
- `GET /api/contracts/{id}`
- `GET /api/contracts/{id}/clauses`
- `GET /api/contracts/{id}/analysis`
- `DELETE /api/contracts/{id}`

## Styling

The project uses Tailwind CSS with a custom color scheme:

```css
Primary: #0F172A (slate-900)
Accent: #3B82F6 (blue-600)
Success: #10B981 (green-600)
Warning: #F59E0B (amber-600)
Danger: #EF4444 (red-600)
```

## State Management

### Zustand AuthStore

```typescript
const { user, isAuthenticated, logout } = useAuthStore();
```

- `user` - Current authenticated user
- `isAuthenticated` - Boolean auth status
- `setUser()` - Update user profile
- `logout()` - Clear auth state
- `hydrateAuth()` - Restore auth from storage

## Building for Production

```bash
npm run build
npm start
```

## Environment Variables

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Application metadata
NEXT_PUBLIC_APP_NAME=ALAS
NEXT_PUBLIC_APP_DESCRIPTION=AI-Powered Legal Contract Analysis Platform
```

## Error Handling

All errors are handled with React Hot Toast notifications:

```typescript
toast.error("Error message");
toast.success("Success message");
toast.loading("Loading...");
```

## Performance Optimizations

- Image optimization with Next.js Image component
- Code splitting and lazy loading
- CSS-in-JS with Tailwind for minimal bundle size
- API request caching and deduplication

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

When adding new features:

1. Follow the existing folder structure
2. Use TypeScript for type safety
3. Implement proper error handling
4. Add loading and error states
5. Ensure responsive design

## License

© 2024 ALAS. All rights reserved.

## Support

For issues or questions, please contact: support@alas.com
