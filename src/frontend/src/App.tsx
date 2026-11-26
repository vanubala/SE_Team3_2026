import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Box, Typography } from "@mui/material";
import { LayoutShell } from "./components/LayoutShell";
// import { ProtectedRoute } from "./components/ProtectedRoute";
import { TerminalLayout } from "./components/LockerTerminal/TerminalLayout";
import { AuthProvider } from "./context/AuthContext";
import { LoginUI } from "./pages/LoginUI";
import { TerminalCodePage } from "./pages/LockerTerminal/CodePage";
import { TerminalDoorPage } from "./pages/LockerTerminal/DoorPage";
import { TerminalHomePage } from "./pages/LockerTerminal/HomePage";

function PlaceholderDashboard({ title }: { title: string }) {
  return (
    <Box
      sx={{
        p: 4,
        bgcolor: "#FFFFFF",
        borderRadius: 3,
        border: "1px solid #E2E8F0",
      }}
    >
      <Typography variant="h5" sx={{ fontWeight: 800 }}>
        {title}
      </Typography>
      <Typography variant="body2" sx={{ color: "text.secondary", mt: 1 }}>
        Ready for implementation.
      </Typography>
    </Box>
  );
}

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Staff Login */}
          <Route path="/login" element={<LoginUI />} />

          {/* Public Kiosk Terminal (UC3 & UC4) */}
          <Route path="/terminal" element={<TerminalLayout />}>
            <Route index element={<TerminalHomePage />} />
            <Route path=":mode" element={<TerminalCodePage />} />
            <Route path="door-open" element={<TerminalDoorPage />} />
          </Route>

          {/* Staff Dashboards (Temporarily unprotected for UI preview) */}
          <Route element={<LayoutShell />}>
            <Route
              path="/courier"
              element={<PlaceholderDashboard title="Courier Dashboard" />}
            />
            <Route
              path="/admin"
              element={<PlaceholderDashboard title="Admin Dashboard" />}
            />
          </Route>

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
