# ALAS Frontend - Project Summary

## 📦 What's Included

A complete, production-ready Next.js frontend for the ALAS legal tech platform.

### Project Specifications

- **Framework**: Next.js 14.0+ with TypeScript
- **Styling**: Tailwind CSS 3.3+
- **State Management**: Zustand 4.4+
- **HTTP Client**: Axios 1.6+ with interceptors
- **Icons**: Lucide React 0.292+
- **Notifications**: React Hot Toast 2.4+
- **Node Version**: 16+ (18+ recommended)

### File Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── auth/
│   │   ├── login/page.tsx        # Login form
│   │   └── signup/page.tsx       # Registration form
│   ├── dashboard/
│   │   ├── layout.tsx            # Dashboard layout
│   │   ├── page.tsx              # Main dashboard
│   │   ├── contracts/
│   │   │   ├── page.tsx          # Contract list
│   │   │   ├── upload/page.tsx   # Upload page
│   │   │   └── [id]/page.tsx     # Contract details
│   │   ├── analytics/page.tsx    # Analytics dashboard
│   │   └── settings/page.tsx     # Settings page
│   ├── globals.css               # Global Tailwind styles
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Home (redirects to login/dashboard)
│
├── components/
│   └── dashboard/
│       ├── Sidebar.tsx           # Navigation sidebar
│       └── Header.tsx            # Top header
│
├── services/
│   └── api.ts                    # Axios client & API calls
│
├── store/
│   └── authStore.ts              # Zustand auth store
│
├── types/                        # TypeScript interfaces (ready for expansion)
│
├── utils/                        # Utility functions (ready for expansion)
│
├── public/                       # Static assets (favicon, etc.)
│
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # (in root ALAS folder)
├── package.json                  # Dependencies & scripts
├── tsconfig.json                 # TypeScript configuration
├── tailwind.config.ts            # Tailwind configuration
├── next.config.js                # Next.js configuration
├── .eslintrc.json                # ESLint rules
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── README.md                     # Frontend documentation
└── UI_FEATURES.md                # UI features reference
```

## 🎨 UI Pages & Routes

### Public Routes (No Auth Required)

| Route          | Component       | Purpose                     |
| -------------- | --------------- | --------------------------- |
| `/`            | page.tsx        | Redirect to login/dashboard |
| `/auth/login`  | login/page.tsx  | User login form             |
| `/auth/signup` | signup/page.tsx | User registration form      |

### Protected Routes (Auth Required)

| Route                         | Component                 | Purpose                          |
| ----------------------------- | ------------------------- | -------------------------------- |
| `/dashboard`                  | dashboard/page.tsx        | Overview dashboard with stats    |
| `/dashboard/contracts`        | contracts/page.tsx        | Contract list with search/filter |
| `/dashboard/contracts/upload` | contracts/upload/page.tsx | PDF upload form                  |
| `/dashboard/contracts/[id]`   | contracts/[id]/page.tsx   | Contract analysis details        |
| `/dashboard/analytics`        | analytics/page.tsx        | Analytics & metrics              |
| `/dashboard/settings`         | settings/page.tsx         | User settings & preferences      |

## 🔐 Authentication System

### Flow

```
User Input
    ↓
Client-side Validation
    ↓
POST /api/auth/signup or /api/auth/login
    ↓
Backend Validation
    ↓
Return JWT Tokens
    ↓
Store in localStorage + Zustand
    ↓
Redirect to Dashboard
```

### Token Management

- **Access Token**: 15 minute validity
- **Refresh Token**: 7 day validity
- **Automatic Refresh**: On 401 responses
- **Auto Logout**: On expired refresh token

## 📱 Responsive Design

### Breakpoints

- **Mobile**: < 768px - Single column, optimized for touch
- **Tablet**: 768px - 1024px - Two columns where applicable
- **Desktop**: > 1024px - Full multi-column layouts

### Mobile-First Features

- Hamburger menu (mobile)
- Touch-friendly buttons (44px minimum)
- Responsive tables (card view on mobile)
- Optimized typography
- Proper spacing and padding

## 🎯 Key Features

### Dashboard

- ✅ Overview stats (4 KPI cards)
- ✅ Recent contracts table
- ✅ Quick access to upload
- ✅ Status indicators

### Contract Management

- ✅ Upload with drag-and-drop
- ✅ PDF validation (type, size, 50MB limit)
- ✅ Contract list with pagination
- ✅ Search and filter functionality
- ✅ Status badges (color-coded)
- ✅ Risk score visualization

### Analysis Viewer

- ✅ Risk score display (0-100%)
- ✅ Issue summary (critical, high, medium)
- ✅ Clause-by-clause breakdown
- ✅ Expandable clause details
- ✅ AI reasoning display
- ✅ Confidence scores
- ✅ Recommended actions

### Analytics

- ✅ Key metrics cards
- ✅ Chart placeholders (ready for integration)
- ✅ Trend visualization setup

### Settings

- ✅ Profile management
- ✅ Password change
- ✅ Notification preferences
- ✅ Logout functionality

## 🔗 Backend Integration Points

### API Endpoints Used

**Authentication**

```
POST /api/auth/signup
POST /api/auth/login
POST /api/auth/refresh
POST /api/auth/logout
GET /api/auth/me
```

**Contracts**

```
POST /api/contracts/upload
GET /api/contracts/list?page=1&limit=10
GET /api/contracts/{id}
GET /api/contracts/{id}/clauses
GET /api/contracts/{id}/analysis
DELETE /api/contracts/{id}
```

### Error Handling

All API errors are displayed via React Hot Toast notifications:

- 400: Bad Request (show detail message)
- 401: Unauthorized (redirect to login)
- 404: Not Found
- 500: Server Error

## 🛠️ Installation & Setup

### Prerequisites

```bash
# Check versions
node --version        # Should be 16+ (18+ recommended)
npm --version         # Should be 8+
```

### Installation Steps

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Set environment variables
cp .env.example .env.local

# 4. Update NEXT_PUBLIC_API_URL if backend is on different host
# NEXT_PUBLIC_API_URL=http://localhost:8000

# 5. Start development server
npm run dev

# 6. Open http://localhost:3000
```

## 📦 Build & Deployment

### Development

```bash
npm run dev           # Start dev server with HMR
npm run type-check    # TypeScript validation
```

### Production

```bash
npm run build         # Build for production
npm start             # Start production server
npm run lint          # Run ESLint
```

### Docker

```bash
# Build image
docker build -t alas-frontend .

# Run container
docker run -p 3000:3000 alas-frontend

# With docker-compose
docker-compose up frontend
```

## 🎨 Design System

### Colors

```
Primary:   #0F172A (slate-900)
Accent:    #3B82F6 (blue-600)
Success:   #10B981 (green-600)
Warning:   #F59E0B (amber-600)
Danger:    #EF4444 (red-600)
Border:    #E2E8F0 (slate-200)
BG:        #F8FAFC (slate-50)
```

### Typography

- **Font**: Inter, system-ui, sans-serif
- **Sizes**: xs(12px), sm(14px), base(16px), lg(18px), xl(20px), 2xl(24px), 3xl(30px)
- **Weights**: 400(normal), 500(medium), 600(semibold), 700(bold)

### Spacing

- **Scale**: 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px
- **Gap utility**: `gap-2`, `gap-4`, `gap-6`, etc.

## 📊 State Management

### Zustand Auth Store

```typescript
const store = useAuthStore()

// State
- user: User | null
- isLoading: boolean
- isAuthenticated: boolean

// Methods
- setUser(user): Update user
- setLoading(bool): Set loading state
- logout(): Clear auth
- hydrateAuth(): Restore from storage
```

## 🔄 API Client Flow

### Request Interceptor

```
1. Get token from localStorage
2. Attach to Authorization header
3. Send request
```

### Response Interceptor

```
1. Check status
2. If 401 & refresh available:
   - Refresh token
   - Retry request
3. If 401 & no refresh:
   - Clear auth
   - Redirect to login
4. Return response
```

## 📝 Environment Variables

```env
# Required
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional
NEXT_PUBLIC_APP_NAME=ALAS
NEXT_PUBLIC_APP_DESCRIPTION=Legal Contract Analysis
```

## ✅ Quality Checklist

- ✅ TypeScript for type safety
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Accessibility preparation (semantic HTML, ARIA labels)
- ✅ Error handling & validation
- ✅ Loading states on all async operations
- ✅ Empty states with helpful messages
- ✅ Form validation (client & server errors)
- ✅ Toast notifications for feedback
- ✅ Secure token management
- ✅ Auto-logout on token expiration

## 🚀 Next Steps for Enhancement

### Short Term

1. [ ] Implement real chart libraries (Recharts/Chart.js)
2. [ ] Add loading skeletons for better UX
3. [ ] Implement search debouncing
4. [ ] Add form persistence (save draft)

### Medium Term

1. [ ] User profile page with avatar
2. [ ] Team management UI
3. [ ] Contract comparison tool
4. [ ] Bulk operations (delete, archive)
5. [ ] Export to PDF/CSV

### Long Term

1. [ ] WebSocket for real-time updates
2. [ ] PWA support with offline mode
3. [ ] Mobile app (React Native)
4. [ ] Advanced analytics dashboard
5. [ ] Contract templates library

## 📞 Support & Resources

- **Frontend README**: See `frontend/README.md`
- **UI Features Guide**: See `frontend/UI_FEATURES.md`
- **Backend README**: See `backend/README.md`
- **Quick Start**: See `QUICKSTART.md`
- **API Docs**: Available at `http://localhost:8000/docs`

## 🎓 Development Tips

### Debugging

```bash
# Enable React Developer Tools
# VS Code extension: ES7+ React/Redux/React-Native snippets

# Check Zustand state
useAuthStore.subscribe(state => console.log(state))
```

### Performance

- Use React DevTools Profiler
- Check bundle size: `npm run build`
- Monitor API requests in Network tab
- Use Next.js Image component for images

### Code Organization

- Keep components small and focused
- Use custom hooks for complex logic
- Centralize API calls in services/api.ts
- Store global state in Zustand

## 📄 License

© 2024 ALAS. All rights reserved.

---

**Version**: 1.0.0  
**Last Updated**: March 2024  
**Status**: Production Ready ✅
