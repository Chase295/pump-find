# Frontend-Architektur im Detail

Das Frontend ist eine React 18 + TypeScript Anwendung mit Material-UI und Zustand für State Management.

---

## Projektstruktur

```
pump-ui/
├── src/
│   ├── App.tsx                 # Root-Komponente, Router, Theme
│   ├── main.tsx                # Entry Point
│   ├── pages/                  # 6 Seiten-Komponenten
│   │   ├── Dashboard.tsx       # Hauptübersicht
│   │   ├── Metrics.tsx         # Prometheus Metriken & Charts
│   │   ├── Phases.tsx          # Phase Management (CRUD)
│   │   ├── Config.tsx          # Runtime-Konfiguration
│   │   ├── Info.tsx            # System-Dokumentation
│   │   └── Logs.tsx            # Service Activity
│   ├── stores/
│   │   └── pumpStore.ts        # Zustand State Management
│   ├── services/
│   │   └── api.ts              # Axios HTTP Client
│   ├── types/
│   │   └── api.ts              # TypeScript Interfaces
│   └── __tests__/              # 101 Tests (vitest + MSW)
├── public/                     # Static Assets
├── index.html                  # HTML Template
├── vite.config.ts              # Build Configuration
├── tsconfig.json               # TypeScript Config
├── package.json                # Dependencies
├── Dockerfile                  # Multi-Stage Build
└── nginx.conf                  # Reverse Proxy Config
```

---

## Komponenten-Hierarchie

```
App.tsx
├── ThemeProvider (MUI Dark Theme)
│   ├── CssBaseline
│   └── Router (BrowserRouter)
│       └── Box (Root Layout)
│           ├── Drawer (Navigation)
│           │   ├── Logo/Title
│           │   └── List (Nav Items)
│           │       ├── Dashboard (/)
│           │       ├── Metriken (/metrics)
│           │       ├── Phasen (/phases)
│           │       ├── Info (/info)
│           │       ├── Konfiguration (/config)
│           │       └── Logs (/logs)
│           └── Box (Main Content)
│               └── Routes
│                   ├── <Dashboard />
│                   ├── <Metrics />
│                   ├── <Phases />
│                   ├── <Config />
│                   ├── <Info />
│                   └── <Logs />
```

---

## App.tsx - Root-Komponente

### Theme-Konfiguration
```typescript
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#00d4ff' },      // Cyan
    secondary: { main: '#ff4081' },    // Pink
    background: {
      default: '#0f0f23',              // Very Dark Blue
      paper: 'rgba(255, 255, 255, 0.05)' // Translucent
    }
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backdropFilter: 'blur(10px)', // Glassmorphism
          borderRadius: 8
        }
      }
    }
  }
});
```

### Responsive Drawer
```typescript
// Mobile: Temporary Drawer (Overlay)
// Desktop: Permanent Drawer (Sidebar)
const isMobile = useMediaQuery(theme.breakpoints.down('md'));

<Drawer
  variant={isMobile ? 'temporary' : 'permanent'}
  open={isMobile ? mobileOpen : true}
  onClose={() => setMobileOpen(false)}
  sx={{ width: 250 }}
>
  {/* Navigation Items */}
</Drawer>
```

---

## Seiten-Komponenten

### Dashboard.tsx

**Zweck:** Hauptübersicht mit Live-Status

**Komponenten:**
- Service Status Card (Healthy/Degraded/Unhealthy)
- Uptime Card (formatiert als "Xd Xh Xm")
- WebSocket Status Chip
- Database Status Chip
- Cache Statistics Paper
- Discovery Statistics Paper
- Tracking Statistics Paper
- Error Alert (bei Fehlern)

**Code-Beispiel:**
```typescript
const Dashboard: React.FC = () => {
  const { health, fetchHealth, startPolling, stopPolling } = usePumpStore();

  useEffect(() => {
    fetchHealth();
    startPolling();
    return () => stopPolling();
  }, []);

  // Uptime formatieren (Performance: useMemo)
  const formattedUptime = useMemo(() => {
    if (!health?.uptime_seconds) return 'N/A';
    const s = health.uptime_seconds;
    const d = Math.floor(s / 86400);
    const h = Math.floor((s % 86400) / 3600);
    const m = Math.floor((s % 3600) / 60);
    return `${d}d ${h}h ${m}m`;
  }, [health?.uptime_seconds]);

  return (
    <Container>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <StatusCard status={health?.status} />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <UptimeCard uptime={formattedUptime} />
        </Grid>
        {/* ... weitere Cards */}
      </Grid>
    </Container>
  );
};
```

### Metrics.tsx

**Zweck:** Prometheus Metriken Visualisierung

**Features:**
- Prometheus Metrics Parser (Text → Object)
- LineChart für Performance über Zeit
- PieChart für Metriken-Verteilung
- Phase Distribution Grid
- Raw Metrics Accordion

**Prometheus Parser:**
```typescript
const parsePrometheusMetrics = (text: string) => {
  const metrics: Record<string, number> = {};
  const lines = text.split('\n');

  for (const line of lines) {
    if (line.startsWith('#') || !line.trim()) continue;

    // Format: metric_name{labels} value
    const match = line.match(/^(\w+)(?:\{[^}]*\})?\s+(\d+(?:\.\d+)?)/);
    if (match) {
      metrics[match[1]] = parseFloat(match[2]);
    }
  }

  return metrics;
};
```

**Charts (Recharts):**
```typescript
<ResponsiveContainer width="100%" height={300}>
  <LineChart data={chartData}>
    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
    <XAxis dataKey="time" stroke="#888" />
    <YAxis stroke="#888" />
    <Tooltip contentStyle={{ backgroundColor: '#1a1a2e' }} />
    <Legend />
    <Line type="monotone" dataKey="coins" stroke="#00d4ff" />
    <Line type="monotone" dataKey="trades" stroke="#4caf50" />
  </LineChart>
</ResponsiveContainer>
```

### Phases.tsx

**Zweck:** Phase Management (CRUD)

**Features:**
- Card-basiertes Layout (statt Tabelle für Mobile)
- Inline-Editing für jede Phase
- Add Phase Dialog
- Delete Phase Dialog mit Confirmation
- System-Phasen (99, 100) sind readonly

**PhaseCard Komponente:**
```typescript
const PhaseCard: React.FC<{ phase: EditingPhase }> = ({ phase }) => {
  const isSystem = phase.id >= 99;

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        {/* Header: ID Chip + System Badge + Actions */}
        <Box display="flex" justifyContent="space-between">
          <Chip label={`Phase ${phase.id}`} color={getPhaseColor(phase.id)} />
          {isSystem && <Chip label="System" color="warning" size="small" />}
          {!isSystem && (
            <Box>
              {phase.isEditing ? (
                <>
                  <IconButton onClick={() => handleSave(phase)}>
                    <SaveIcon />
                  </IconButton>
                  <IconButton onClick={() => handleCancel(phase)}>
                    <CancelIcon />
                  </IconButton>
                </>
              ) : (
                <>
                  <IconButton onClick={() => handleEdit(phase)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => handleDelete(phase)}>
                    <DeleteIcon />
                  </IconButton>
                </>
              )}
            </Box>
          )}
        </Box>

        {/* Name */}
        {phase.isEditing ? (
          <TextField value={phase.name} onChange={...} />
        ) : (
          <Typography>{phase.name}</Typography>
        )}

        {/* Stats Grid: Interval | Min Age | Max Age */}
        <Grid container spacing={2}>
          <Grid size={{ xs: 4 }}>
            {phase.isEditing ? (
              <TextField type="number" value={phase.interval_seconds} />
            ) : (
              <Typography>{phase.interval_seconds}s</Typography>
            )}
          </Grid>
          {/* ... Min Age, Max Age */}
        </Grid>
      </CardContent>
    </Card>
  );
};
```

### Config.tsx

**Zweck:** Runtime-Konfiguration ändern

**Features:**
- Card-basierte Formulargruppen
- Nur geänderte Felder werden gesendet
- Passwort-Maskierung in DB_DSN
- Success/Error Messages mit Auto-Dismiss

**Smart Update Logic:**
```typescript
const handleSave = async () => {
  // Nur geänderte Felder ermitteln
  const changes: Partial<ConfigUpdateRequest> = {};

  if (formData.n8n_webhook_url !== originalConfig?.n8n_webhook_url) {
    changes.n8n_webhook_url = formData.n8n_webhook_url;
  }
  if (formData.batch_size !== originalConfig?.batch_size) {
    changes.batch_size = formData.batch_size;
  }
  // ... weitere Felder

  if (Object.keys(changes).length === 0) {
    setError('Keine Änderungen erkannt');
    return;
  }

  try {
    await pumpApi.updateConfig(changes);
    setSuccess('Konfiguration gespeichert');
    fetchConfig(); // Refresh
  } catch (err) {
    setError('Fehler beim Speichern');
  }
};
```

### Info.tsx

**Zweck:** System-Dokumentation (interaktiv)

**Features:**
- Accordion-basierte Struktur (Mobile-freundlich)
- Live-Stats Bar oben
- Wiederverwendbare Komponenten: CodeBlock, ConfigItem, PhaseItem, ApiEndpoint
- Responsive Typography

**Custom Components:**
```typescript
const CodeBlock: React.FC<{ children: ReactNode }> = ({ children }) => (
  <Box sx={{
    bgcolor: 'rgba(0,0,0,0.3)',
    p: { xs: 1.5, sm: 2 },
    borderRadius: 1,
    overflowX: 'auto'
  }}>
    <Typography component="pre" sx={{
      fontFamily: 'monospace',
      fontSize: { xs: '0.7rem', sm: '0.8rem' },
      whiteSpace: 'pre-wrap'
    }}>
      {children}
    </Typography>
  </Box>
);

const ApiEndpoint: React.FC<{ method: string; path: string; desc: string }> = (props) => (
  <Box sx={{ mb: 2, p: 2, bgcolor: 'rgba(0,0,0,0.2)', borderRadius: 1 }}>
    <Chip
      label={props.method}
      size="small"
      sx={{
        bgcolor: props.method === 'GET' ? '#4caf50' :
                 props.method === 'PUT' ? '#ff9800' :
                 props.method === 'POST' ? '#2196f3' : '#f44336'
      }}
    />
    <Typography sx={{ fontFamily: 'monospace' }}>{props.path}</Typography>
    <Typography variant="body2">{props.desc}</Typography>
  </Box>
);
```

### Logs.tsx

**Zweck:** Service Activity Log

**Features:**
- Health-Daten in Log-Format konvertiert
- Auto-Refresh Toggle
- Konfigurierbares Refresh-Intervall
- Download als TXT-Datei

---

## State Management (Zustand)

### pumpStore.ts

```typescript
interface PumpStore {
  // State
  health: HealthResponse | null;
  config: ConfigResponse | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;

  // Actions
  fetchHealth: () => Promise<void>;
  fetchConfig: () => Promise<void>;
  updateConfig: (data: ConfigUpdateRequest) => Promise<void>;
  startPolling: () => void;
  stopPolling: () => void;
}

export const usePumpStore = create<PumpStore>()(
  devtools((set, get) => ({
    health: null,
    config: null,
    isLoading: false,
    error: null,
    lastUpdated: null,

    fetchHealth: async () => {
      set({ isLoading: true });
      try {
        const health = await pumpApi.getHealth();
        set({
          health,
          isLoading: false,
          error: null,
          lastUpdated: new Date()
        });
      } catch (err) {
        set({
          health: disconnectedHealth,
          isLoading: false,
          error: err instanceof Error ? err.message : 'API unreachable'
        });
      }
    },

    startPolling: () => {
      const intervalId = setInterval(() => {
        get().fetchHealth();
        get().fetchConfig();
      }, 5000);

      // Store interval ID for cleanup
      (window as any).__pumpPollingId = intervalId;
    },

    stopPolling: () => {
      const intervalId = (window as any).__pumpPollingId;
      if (intervalId) {
        clearInterval(intervalId);
      }
    }
  }))
);
```

### Fallback Health State
```typescript
const disconnectedHealth: HealthResponse = {
  status: 'unhealthy',
  ws_connected: false,
  db_connected: false,
  uptime_seconds: 0,
  last_message_ago: null,
  reconnect_count: 0,
  last_error: 'Service nicht erreichbar',
  cache_stats: { total_coins: 0, activated_coins: 0, expired_coins: 0 },
  tracking_stats: { active_coins: 0, total_trades: 0, total_metrics_saved: 0 },
  discovery_stats: { total_coins_discovered: 0, n8n_available: false, n8n_buffer_size: 0 }
};
```

---

## API Client (api.ts)

### Axios Setup
```typescript
const api = axios.create({
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
});

// Dynamic Base URL
api.interceptors.request.use((config) => {
  if (!config.url?.startsWith('http')) {
    config.baseURL = window.location.origin;
  }
  return config;
});

// Error Logging
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);
```

### API Methods
```typescript
export const pumpApi = {
  // Health & Config
  getHealth: () => api.get<HealthResponse>('/api/health').then(r => r.data),
  getConfig: () => api.get<ConfigResponse>('/api/config').then(r => r.data),
  updateConfig: (data: ConfigUpdateRequest) =>
    api.put<ConfigUpdateResponse>('/api/config', data).then(r => r.data),

  // Metrics & Streams
  getMetrics: () => api.get<string>('/api/metrics').then(r => r.data),
  getStreamStats: () => api.get<StreamStatsResponse>('/api/database/streams/stats').then(r => r.data),

  // Phase Management
  getPhases: () => api.get<PhasesResponse>('/api/database/phases').then(r => r.data),
  updatePhase: (id: number, data: PhaseUpdateRequest) =>
    api.put<PhaseUpdateResponse>(`/api/database/phases/${id}`, data).then(r => r.data),
  createPhase: (data: PhaseCreateRequest) =>
    api.post<PhaseCreateResponse>('/api/database/phases', data).then(r => r.data),
  deletePhase: (id: number) =>
    api.delete<PhaseDeleteResponse>(`/api/database/phases/${id}`).then(r => r.data),
};
```

---

## Responsive Design Patterns

### MUI Breakpoints
```typescript
// xs: 0px    (Mobile Phone)
// sm: 600px  (Tablet Portrait)
// md: 960px  (Tablet Landscape / Small Desktop)
// lg: 1280px (Desktop)
// xl: 1920px (Large Desktop)
```

### Responsive Patterns
```typescript
// 1. Conditional Typography
<Typography variant={isMobile ? 'h6' : 'h4'}>

// 2. Responsive Spacing
sx={{ p: { xs: 1, sm: 2, md: 3 } }}

// 3. Responsive Font Size
sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}

// 4. Flex Direction Switch
sx={{ flexDirection: { xs: 'column', md: 'row' } }}

// 5. Grid Layout
<Grid size={{ xs: 12, sm: 6, md: 4 }}>

// 6. useMediaQuery Hook
const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
```

---

## Build & Deployment

### Vite Build
```bash
npm run build
# Output: dist/ (optimized bundle)
```

### Multi-Stage Dockerfile
```dockerfile
# Stage 1: Build
FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --include=dev
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=0 /app/dist /usr/share/nginx/html
EXPOSE 80
```

---

## Weiterführende Dokumentation

- [API Endpunkte](../api/endpoints.md)
- [Frontend Tests](../testing/frontend.md)
- [Docker Deployment](../deployment/docker.md)
