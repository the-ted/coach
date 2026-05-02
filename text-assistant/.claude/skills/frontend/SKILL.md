---
name: frontend
description: Write production-ready React 18+ frontend code with TypeScript, Material-UI, Redux Toolkit, Formik, protected routes, and styled components. Use when creating UI components, forms, or client-side features.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Frontend Development Instructions

When writing frontend code, follow these patterns:

## Architecture

**Always use this structure:**
```
src/
├── components/
│   ├── common/          # Reusable UI (Button, Card, etc.)
│   └── layout/          # Layout wrappers (Header, Sidebar)
├── features/
│   └── [feature]/
│       ├── components/  # Feature-specific components
│       ├── slices/      # Redux slices
│       ├── hooks/       # Custom hooks
│       └── index.ts     # Exports
├── services/            # RTK Query API services
├── store/               # Redux store config
├── utils/               # Helper functions
└── App.tsx
```

## Component Structure

Write all components with TypeScript and proper documentation:

```typescript
import { FC, memo } from 'react';
import { Box, Typography } from '@mui/material';
import { SxProps, Theme } from '@mui/material/styles';

interface ItemCardProps {
  id: string;
  title: string;
  description?: string;
  onClick?: (id: string) => void;
  sx?: SxProps<Theme>;
}

/**
 * ItemCard displays item information in a card format.
 */
export const ItemCard: FC<ItemCardProps> = memo(({
  id,
  title,
  description,
  onClick,
  sx
}) => {
  const handleClick = () => onClick?.(id);

  return (
    <Box
      onClick={handleClick}
      sx={{
        p: 2,
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
        cursor: onClick ? 'pointer' : 'default',
        '&:hover': onClick ? { bgcolor: 'action.hover' } : {},
        ...sx,
      }}
    >
      <Typography variant="h6">{title}</Typography>
      {description && (
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
      )}
    </Box>
  );
});

ItemCard.displayName = 'ItemCard';
```

**Rules:**
- Use `FC` and `memo` for components
- Define props interface with JSDoc
- Use optional chaining (`?.`) for optional callbacks
- Spread `sx` prop last for override ability
- Add `displayName` for debugging

## Styled Components with MUI

Create reusable styled components with `styled()`:

```typescript
import { styled } from '@mui/material/styles';
import { Card, Button, Box } from '@mui/material';

// Card with hover effect
export const StyledCard = styled(Card)(({ theme }) => ({
  padding: theme.spacing(3),
  borderRadius: theme.shape.borderRadius * 2,
  transition: 'all 0.3s ease',
  '&:hover': {
    boxShadow: theme.shadows[8],
    transform: 'translateY(-4px)',
  },
}));

// Gradient button
export const GradientButton = styled(Button)(({ theme }) => ({
  background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
  color: theme.palette.primary.contrastText,
  padding: theme.spacing(1.5, 4),
  borderRadius: theme.shape.borderRadius * 2,
  textTransform: 'none',
  fontWeight: 600,
  '&:hover': {
    background: `linear-gradient(45deg, ${theme.palette.primary.dark}, ${theme.palette.primary.main})`,
  },
}));

// Flexible layout with props
interface FlexBoxProps {
  direction?: 'row' | 'column';
  gap?: number;
}

export const FlexBox = styled(Box, {
  shouldForwardProp: (prop) => !['direction', 'gap'].includes(prop as string),
})<FlexBoxProps>(({ theme, direction = 'row', gap = 2 }) => ({
  display: 'flex',
  flexDirection: direction,
  gap: theme.spacing(gap),
}));
```

**Rules:**
- Use theme for all spacing and colors
- Add transitions for interactive elements
- Use `shouldForwardProp` to filter custom props
- Keep styles composable

## Forms with Formik + Yup

Always use Formik for forms with Yup validation:

```typescript
import { Formik, Form } from 'formik';
import * as Yup from 'yup';
import { TextField, Button, Box } from '@mui/material';

const itemSchema = Yup.object({
  name: Yup.string()
    .required('Name is required')
    .min(3, 'Name must be at least 3 characters'),
  email: Yup.string()
    .email('Invalid email')
    .required('Email is required'),
});

interface FormValues {
  name: string;
  email: string;
}

export const ItemForm: FC = () => {
  const handleSubmit = async (values: FormValues) => {
    // Submit logic
  };

  return (
    <Formik
      initialValues={{ name: '', email: '' }}
      validationSchema={itemSchema}
      onSubmit={handleSubmit}
    >
      {({ values, errors, touched, handleChange, handleBlur, isSubmitting }) => (
        <Form>
          <Box display="flex" flexDirection="column" gap={2}>
            <TextField
              name="name"
              label="Name"
              value={values.name}
              onChange={handleChange}
              onBlur={handleBlur}
              error={touched.name && Boolean(errors.name)}
              helperText={touched.name && errors.name}
              fullWidth
            />
            <TextField
              name="email"
              label="Email"
              type="email"
              value={values.email}
              onChange={handleChange}
              onBlur={handleBlur}
              error={touched.email && Boolean(errors.email)}
              helperText={touched.email && errors.email}
              fullWidth
            />
            <Button
              type="submit"
              variant="contained"
              disabled={isSubmitting}
            >
              Submit
            </Button>
          </Box>
        </Form>
      )}
    </Formik>
  );
};
```

## Redux Store Setup

Configure store with RTK and RTK Query:

```typescript
// store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { authApi } from '../services/authApi';
import authReducer from '../features/auth/slices/authSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    [authApi.reducerPath]: authApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(authApi.middleware),
});

setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

```typescript
// store/hooks.ts
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from './index';

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
```

## Redux Slice Pattern

```typescript
// features/auth/slices/authSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { RootState } from '../../../store';

interface User {
  id: string;
  email: string;
  role: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}

const initialState: AuthState = {
  user: null,
  accessToken: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (
      state,
      action: PayloadAction<{ user: User; accessToken: string; refreshToken: string }>
    ) => {
      state.user = action.payload.user;
      state.accessToken = action.payload.accessToken;
      state.refreshToken = action.payload.refreshToken;
      state.isAuthenticated = true;

      localStorage.setItem('access_token', action.payload.accessToken);
      localStorage.setItem('refresh_token', action.payload.refreshToken);
      localStorage.setItem('user', JSON.stringify(action.payload.user));
    },
    logout: (state) => {
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.isAuthenticated = false;

      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    },
  },
});

export const { setCredentials, logout } = authSlice.actions;
export default authSlice.reducer;

// Selectors
export const selectCurrentUser = (state: RootState) => state.auth.user;
export const selectIsAuthenticated = (state: RootState) => state.auth.isAuthenticated;
```

## RTK Query API Service

```typescript
// services/authApi.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../store';

interface LoginRequest {
  email: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api',
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.accessToken;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  endpoints: (builder) => ({
    login: builder.mutation<TokenResponse, LoginRequest>({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
    }),
    getMe: builder.query<User, void>({
      query: () => '/auth/me',
    }),
    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/auth/logout',
        method: 'POST',
      }),
    }),
  }),
});

export const { useLoginMutation, useGetMeQuery, useLogoutMutation } = authApi;
```

## Authentication Flow

**Complete authentication and authorization flow:**

1. **Route Protection**: All routes except `/login` are protected by `PrivateRoute`
2. **Token Storage**: JWT tokens stored in localStorage (`access_token`, `refresh_token`, `user`)
3. **Auto-Redirect**: 401 errors automatically redirect to `/login`
4. **API Authentication**: All API calls automatically attach JWT token from localStorage
5. **Landing Page**: `/` is the main landing page (protected, redirects to `/login` if not authenticated)

**Token Auto-Attachment:**

```typescript
// services/api.ts - Automatically attach JWT to all requests
function getAuthToken(): string | null {
  return localStorage.getItem('access_token')
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const token = getAuthToken()
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options?.headers,
  }

  // Auto-attach Bearer token if available
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(url, { ...options, headers })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    const detail = errorData.detail
    const message = typeof detail === 'object' && detail?.message
      ? detail.message
      : (typeof detail === 'string' ? detail : `HTTP ${response.status}`)

    throw new APIError(message, response.status, errorData)
  }

  return response.json()
}
```

**401 Handling in Contexts:**

```typescript
// ConfigContext checks auth and handles 401
export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const accessToken = useSelector((state: RootState) => state.auth.accessToken)

  const loadConfig = async () => {
    // Only load config if user is authenticated
    if (!accessToken) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      const data = await api.getConfig()
      setConfig(data)
    } catch (err) {
      // Handle 401 Unauthorized - redirect to login
      if (err instanceof APIError && err.status === 401) {
        navigate('/login', { replace: true })
        return
      }
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadConfig()
  }, [accessToken]) // Re-fetch when token changes
}
```

**Route Configuration:**

```typescript
// AppRoutes.tsx
export const AppRoutes: FC = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected routes */}
      <Route
        path="/profile"
        element={
          <PrivateRoute>
            <LayoutWrapper>
              <ProfilePage />
            </LayoutWrapper>
          </PrivateRoute>
        }
      />
      <Route
        path="/*"
        element={
          <PrivateRoute>
            <App />
          </PrivateRoute>
        }
      />

      {/* Fallback - redirect to login */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
};
```

## Protected Routes

Create PrivateRoute wrapper for authenticated routes:

```typescript
// features/auth/components/PrivateRoute.tsx
import { FC, ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { CircularProgress, Box } from '@mui/material';

interface PrivateRouteProps {
  children: ReactNode;
  requiredRole?: string | string[];
  redirectTo?: string;
}

export const PrivateRoute: FC<PrivateRouteProps> = ({
  children,
  requiredRole,
  redirectTo = '/login',
}) => {
  const { isAuthenticated, user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  if (requiredRole && user) {
    const roles = Array.isArray(requiredRole) ? requiredRole : [requiredRole];
    if (!roles.includes(user.role)) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return <>{children}</>;
};
```

## useAuth Hook

```typescript
// features/auth/hooks/useAuth.ts
import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../../store/hooks';
import {
  setCredentials,
  logout as logoutAction,
  selectIsAuthenticated,
  selectCurrentUser,
} from '../slices/authSlice';
import { useLoginMutation, useLogoutMutation } from '../../../services/authApi';

export const useAuth = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  const user = useAppSelector(selectCurrentUser);

  const [loginMutation, { isLoading: isLoggingIn }] = useLoginMutation();
  const [logoutMutation] = useLogoutMutation();

  const login = useCallback(async (email: string, password: string) => {
    try {
      const result = await loginMutation({ email, password }).unwrap();
      dispatch(setCredentials({
        user: result.user,
        accessToken: result.access_token,
        refreshToken: result.refresh_token,
      }));
      return { success: true };
    } catch (error: any) {
      return { success: false, error: error.data?.detail || 'Login failed' };
    }
  }, [loginMutation, dispatch]);

  const logout = useCallback(async () => {
    try {
      await logoutMutation().unwrap();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      dispatch(logoutAction());
      navigate('/login');
    }
  }, [logoutMutation, dispatch, navigate]);

  return {
    isAuthenticated,
    user,
    isLoading: false,
    isLoggingIn,
    login,
    logout,
  };
};
```

## App Routing

```typescript
// AppRoutes.tsx
import { FC } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { PrivateRoute } from './features/auth/components/PrivateRoute';
import { LoginPage } from './features/auth/components/LoginPage';

export const AppRoutes: FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        }
      />

      <Route
        path="/admin/*"
        element={
          <PrivateRoute requiredRole="admin">
            <AdminPanel />
          </PrivateRoute>
        }
      />

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};
```

## Custom Hooks Pattern

```typescript
// hooks/useDebounce.ts
import { useEffect, useState } from 'react';

export const useDebounce = <T,>(value: T, delay: number = 500): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};
```

## Dependencies

**Always include in package.json:**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.1",
    "@mui/material": "^5.15.5",
    "@emotion/react": "^11.11.3",
    "@emotion/styled": "^11.11.0",
    "@reduxjs/toolkit": "^2.0.1",
    "react-redux": "^9.0.4",
    "formik": "^2.4.5",
    "yup": "^1.3.3"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "typescript": "^5.3.3",
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.1"
  }
}
```

## Key Reminders

- ✅ Use TypeScript for all components
- ✅ Use MUI components consistently
- ✅ Use `styled()` for custom styled components
- ✅ Use Formik + Yup for all forms
- ✅ Use Redux Toolkit for global state
- ✅ Use RTK Query for API calls
- ✅ Create PrivateRoute wrapper for protected routes
- ✅ Use custom hooks for reusable logic
- ✅ Add proper TypeScript interfaces
- ✅ Include JSDoc comments on components
- ✅ Use `memo` for components that don't need frequent re-renders
- ✅ Keep components focused and single-purpose
- ✅ Export from feature index.ts files
- ✅ Use global snackbar slice for notifications
- ✅ Use global loading slice for full-page loaders
- ✅ Use Suspense with LoadingFallback for code splitting
- ✅ Add GlobalSnackbar and GlobalLoader to App.tsx
- ✅ Always use BCG theme colors (BCG Green #009639 as primary)
- ✅ Use gradient buttons for primary actions
- ✅ Include BCG logo on login and branded pages
- ✅ Use consistent card styling with subtle shadows
- ✅ Apply proper spacing and BCG typography

## Reusable UI Components

### Global Snackbar/Toast Notifications

Create Redux slice for snackbar:

```typescript
// features/ui/slices/snackbarSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SnackbarState {
  open: boolean;
  message: string;
  severity: 'success' | 'error' | 'warning' | 'info';
}

const snackbarSlice = createSlice({
  name: 'snackbar',
  initialState: { open: false, message: '', severity: 'info' as const },
  reducers: {
    showSnackbar: (state, action: PayloadAction<{ message: string; severity?: 'success' | 'error' | 'warning' | 'info' }>) => {
      state.open = true;
      state.message = action.payload.message;
      state.severity = action.payload.severity || 'info';
    },
    hideSnackbar: (state) => { state.open = false; },
  },
});

export const { showSnackbar, hideSnackbar } = snackbarSlice.actions;
export default snackbarSlice.reducer;
```

Global snackbar component:

```typescript
// components/common/GlobalSnackbar.tsx
import { Snackbar, Alert } from '@mui/material';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { hideSnackbar } from '@/features/ui/slices/snackbarSlice';

export const GlobalSnackbar = () => {
  const dispatch = useAppDispatch();
  const { open, message, severity } = useAppSelector((state) => state.snackbar);

  return (
    <Snackbar open={open} autoHideDuration={6000} onClose={() => dispatch(hideSnackbar())} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
      <Alert onClose={() => dispatch(hideSnackbar())} severity={severity} variant="filled">{message}</Alert>
    </Snackbar>
  );
};
```

**Usage:**
```typescript
dispatch(showSnackbar({ message: 'Success!', severity: 'success' }));
```

### Global Loading State

```typescript
// features/ui/slices/loadingSlice.ts
const loadingSlice = createSlice({
  name: 'loading',
  initialState: { isLoading: false, message: '' },
  reducers: {
    setLoading: (state, action: PayloadAction<{ loading: boolean; message?: string }>) => {
      state.isLoading = action.payload.loading;
      state.message = action.payload.message || '';
    },
  },
});
```

```typescript
// components/common/GlobalLoader.tsx
import { Backdrop, CircularProgress, Typography, Box } from '@mui/material';

export const GlobalLoader = () => {
  const { isLoading, message } = useAppSelector((state) => state.loading);
  return (
    <Backdrop open={isLoading} sx={{ zIndex: 9999 }}>
      <Box display="flex" flexDirection="column" alignItems="center" gap={2}>
        <CircularProgress color="inherit" />
        {message && <Typography>{message}</Typography>}
      </Box>
    </Backdrop>
  );
};
```

### Suspense with Loading Fallback

```typescript
// components/common/LoadingFallback.tsx
export const LoadingFallback = ({ message = 'Loading...' }) => (
  <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px" gap={2}>
    <CircularProgress />
    <Typography>{message}</Typography>
  </Box>
);

// Usage with lazy loading
const Dashboard = lazy(() => import('./Dashboard'));

<Suspense fallback={<LoadingFallback message="Loading Dashboard..." />}>
  <Dashboard />
</Suspense>
```

**Add to store:**
```typescript
export const store = configureStore({
  reducer: {
    auth: authReducer,
    config: configReducer,
    snackbar: snackbarReducer,
    loading: loadingReducer,
    [authApi.reducerPath]: authApi.reducer,
    [configApi.reducerPath]: configApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware()
      .concat(authApi.middleware)
      .concat(configApi.middleware),
});
```

## Config Management Pattern

Always use Redux slice + RTK Query for configuration management:

**Config Slice (features/config/slices/configSlice.ts):**
```typescript
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { SystemConfig } from '@/shared/types';

interface ConfigState {
  config: SystemConfig | null;
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
}

const configSlice = createSlice({
  name: 'config',
  initialState: {
    config: null,
    loading: false,
    error: null,
    lastUpdated: null,
  } as ConfigState,
  reducers: {
    setConfig: (state, action: PayloadAction<SystemConfig>) => {
      state.config = action.payload;
      state.loading = false;
      state.error = null;
      state.lastUpdated = new Date().toISOString();
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
      state.loading = false;
    },
  },
});
```

**Config API (features/config/services/configApi.ts):**
```typescript
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '@/store';
import type { SystemConfig, AgentConfig } from '@/shared/types';

export const configApi = createApi({
  reducerPath: 'configApi',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api',
    prepareHeaders: (headers, { getState }) => {
      // Attach JWT token from auth state (config endpoints require auth)
      const token = (getState() as RootState).auth.accessToken;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Config', 'Agents', 'AgentDetail'],
  endpoints: (builder) => ({
    getConfig: builder.query<SystemConfig, void>({
      query: () => '/config',
      providesTags: ['Config'],
    }),
    // Get agent summaries (no commands/loops) for list/sidebar
    getAgents: builder.query<AgentSummary[], void>({
      query: () => '/agents',
      providesTags: ['Agents'],
    }),
    // Get full agent details (includes commands/loops) for detail view
    getAgentDetail: builder.query<AgentConfig, string>({
      query: (agentId) => `/agents/${agentId}`,
      providesTags: (result, error, agentId) => [{ type: 'AgentDetail', id: agentId }],
    }),
    reloadConfig: builder.mutation<{ status: string }, void>({
      query: () => ({
        url: '/config/reload',
        method: 'POST',
      }),
      invalidatesTags: ['Config', 'Agents', 'AgentDetail'],
    }),
  }),
});

export const {
  useGetConfigQuery,
  useGetAgentsQuery,
  useGetAgentDetailQuery,
  useReloadConfigMutation
} = configApi;
```

**Agents Hook (features/config/hooks/useAgents.ts):**
```typescript
// Returns agent summaries (without commands/loops)
import { useGetAgentsQuery } from '../services/configApi';

export const useAgents = () => {
  const { data: agents, error, isLoading, refetch } = useGetAgentsQuery();

  return {
    agents: agents || [], // AgentSummary[]
    loading: isLoading,
    error: error ? 'Failed to load agents' : null,
    refetch,
  };
};
```

**Config Hook (features/config/hooks/useConfigData.ts):**
```typescript
import { useDispatch, useSelector } from 'react-redux';
import { useEffect } from 'react';
import type { RootState } from '@/store';
import { setConfig, setLoading, setError } from '../slices/configSlice';
import { useGetConfigQuery } from '../services/configApi';

export const useConfigData = () => {
  const dispatch = useDispatch();
  const { config, loading, error } = useSelector((state: RootState) => state.config);
  const { data, error: apiError, isLoading, refetch } = useGetConfigQuery();

  useEffect(() => {
    if (data) dispatch(setConfig(data));
  }, [data, dispatch]);

  useEffect(() => {
    if (apiError) {
      const errorMessage = 'message' in apiError ? apiError.message : 'Failed to load config';
      dispatch(setError(errorMessage));
    }
  }, [apiError, dispatch]);

  return { config, loading, error, refetch };
};
```

**Usage:**
```typescript
// 1. System config (theme, navigation, system info)
import { useConfigData } from '@/features/config';

function MyComponent() {
  const { config, loading, error } = useConfigData();

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;
  if (!config) return null;

  return <div>{config.system.name}</div>;
}

// 2. Agent list view - shows all agents
import { useAgents } from '@/features/config';
import { AgentListView } from '@/features/agents';

function App() {
  const { agents } = useAgents(); // Summaries only

  return <AgentListView onSelectAgent={(id) => navigate(`/?agent=${id}`)} />;
}

// 3. Agent detail view - fetches full details on demand
import { useGetAgentDetailQuery } from '@/features/config';

function AgentView({ agentId }: { agentId: string }) {
  const { data: agent, isLoading } = useGetAgentDetailQuery(agentId);

  if (isLoading) return <div>Loading agent details...</div>;
  if (!agent) return <div>Agent not found</div>;

  return (
    <div>
      <h1>{agent.name}</h1>
      {agent.commands.map(cmd => <CommandTile key={cmd.id} command={cmd} />)}
    </div>
  );
}

// 4. Sidebar - agent summaries for navigation
import { useAgents } from '@/features/config';

function Sidebar() {
  const { agents, loading, error } = useAgents();

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <nav>
      {agents.map(agent => (
        <AgentNavItem key={agent.id} agent={agent} />
      ))}
    </nav>
  );
}
```

**Important Agent Flow:**
- `/api/config` returns system info, UI theme (NO agents, NO backend)
- `/api/agents` returns agent summaries (id, name, description, icon, color)
- `/api/agents/{id}` returns full agent details (includes commands/loops)
- Landing page (`/`) shows AgentListView initially
- Click agent → URL changes to `/?agent=agent_id`
- App reads URL param → Calls `/api/agents/{id}` → Shows AgentView with details
- Sidebar always shows agent summaries from `/api/agents`
- Use `useAgents()` for list/sidebar, `useGetAgentDetailQuery(id)` for details

**Add to App.tsx:**
```typescript
<GlobalSnackbar />
<GlobalLoader />
```

## BCG Theme & Branding

### Theme Configuration

Always use BCG brand colors throughout the application:

```typescript
// theme/index.ts
import { createTheme } from '@mui/material/styles';

const BCG_GREEN = '#009639';
const BCG_DARK_GREEN = '#007A2D';
const BCG_CHARCOAL = '#2D3436';
const BCG_GRAY = '#636E72';

export const theme = createTheme({
  palette: {
    primary: {
      main: BCG_GREEN,
      dark: BCG_DARK_GREEN,
      light: '#00B04C',
      contrastText: '#ffffff',
    },
    secondary: {
      main: BCG_CHARCOAL,
      dark: '#1A1C1D',
      light: BCG_GRAY,
    },
    background: {
      default: '#F8F9FA',
      paper: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", sans-serif',
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        containedPrimary: {
          background: `linear-gradient(135deg, ${BCG_GREEN} 0%, ${BCG_DARK_GREEN} 100%)`,
        },
      },
    },
  },
});
```

**Usage in App:**
```typescript
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { theme } from './theme';

<ThemeProvider theme={theme}>
  <CssBaseline />
  <App />
</ThemeProvider>
```

### BCG Logo Component

```typescript
export const BCGLogo = ({ size = 50 }) => (
  <Box
    sx={{
      width: size,
      height: size,
      borderRadius: '50%',
      bgcolor: 'primary.main',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    <Typography
      variant={size > 40 ? 'h6' : 'body1'}
      color="white"
      fontWeight="bold"
    >
      BCG
    </Typography>
  </Box>
);
```

### Gradient Buttons

```typescript
// Always use gradient for primary actions
<Button
  variant="contained"
  color="primary"
  sx={{
    background: 'linear-gradient(135deg, #009639 0%, #007A2D 100%)',
    '&:hover': {
      background: 'linear-gradient(135deg, #007A2D 0%, #009639 100%)',
    },
  }}
>
  Primary Action
</Button>
```

### Brand Colors Usage

- **Primary Actions**: BCG Green (#009639)
- **Secondary Actions**: BCG Charcoal (#2D3436)
- **Text Primary**: BCG Charcoal
- **Text Secondary**: BCG Gray (#636E72)
- **Backgrounds**: White (#FFFFFF) or Light Gray (#F8F9FA)
- **Success**: BCG Green
- **Cards**: White with subtle shadow

### Consistent Styling

**Cards:**
```typescript
<Card
  sx={{
    borderRadius: 3,
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
    '&:hover': {
      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.12)',
    },
  }}
>
```

**Page Headers:**
```typescript
<Box sx={{ mb: 3 }}>
  <Typography variant="h4" fontWeight="600" gutterBottom>
    Page Title
  </Typography>
  <Typography variant="body2" color="text.secondary">
    Page description
  </Typography>
</Box>
```

**Role Badges:**
```typescript
// Color-coded by role
const getRoleColor = (role: string) => {
  switch (role) {
    case 'super_admin': return 'error';
    case 'admin': return 'warning';
    default: return 'primary';
  }
};

<Chip label={role} color={getRoleColor(role)} size="small" />
```
