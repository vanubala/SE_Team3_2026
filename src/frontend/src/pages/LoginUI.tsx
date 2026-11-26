import { useState, type SubmitEvent } from "react";
import { Link as RouterLink, Navigate, useNavigate } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  Container,
  Divider,
  Link,
  Stack,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import { LoginForm } from "../components/Auth/LoginForm";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../types/domain";

export function LoginUI() {
  const { user, isAuthenticated, login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (isAuthenticated && user) {
    return (
      <Navigate to={user.role === "ADMIN" ? "/admin" : "/courier"} replace />
    );
  }

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!email.trim() || !password || loading) return;

    setLoading(true);
    setError(null);

    try {
      const authenticatedUser = await login(email, password);
      navigate(authenticatedUser.role === "ADMIN" ? "/admin" : "/courier", {
        replace: true,
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to sign in. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={styles.pageWrapper}>
      <Container maxWidth="xs">
        <Card elevation={2} sx={styles.loginCard}>
          <Box sx={styles.topAccentBar} />

          <CardContent sx={styles.cardBody}>
            <Stack spacing={0.5} sx={styles.headerBlock}>
              <Box sx={styles.logoBadge}>Smart Parcel Locker</Box>
              <Typography variant="h5" sx={styles.title}>
                Login Portal
              </Typography>
              <Typography variant="body2" sx={styles.subtitle}>
                Sign in as a Courier or System Administrator
              </Typography>
            </Stack>

            <LoginForm
              email={email}
              password={password}
              loading={loading}
              error={error}
              onEmailChange={setEmail}
              onPasswordChange={setPassword}
              onSubmit={handleSubmit}
            />

            <Divider sx={styles.divider} />

            <Box sx={styles.footerRow}>
              <Typography variant="caption" sx={styles.footerText}>
                Forgot your password ? - {" "}
              </Typography>
              <Link
                component={RouterLink}
                to="/terminal"
                underline="hover"
                sx={styles.kioskLink}
              >
                Open Kiosk Terminal
              </Link>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  pageWrapper: {
    minHeight: "100vh",
    bgcolor: "#F8FAFC",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    p: 2,
  },
  loginCard: {
    borderRadius: 3,
    overflow: "hidden",
    border: "1px solid #CBD5E1",
    boxShadow: "0 10px 28px rgba(15, 23, 42, 0.06)",
    bgcolor: "#FFFFFF",
  },
  topAccentBar: {
    height: 6,
    bgcolor: "primary.main",
  },
  cardBody: {
    p: { xs: 3, sm: 4 },
  },
  headerBlock: {
    alignItems: "center",
    textAlign: "center",
    mb: 3,
  },
  logoBadge: {
    bgcolor: "primary.main",
    color: "#FFFFFF",
    fontWeight: 800,
    fontSize: "0.85rem",
    letterSpacing: 1.2,
    px: 1.5,
    py: 0.5,
    borderRadius: 1.5,
    mb: 1,
  },
  title: {
    fontWeight: 800,
    color: "text.primary",
  },
  subtitle: {
    color: "text.secondary",
  },
  divider: {
    my: 2.5,
  },
  footerRow: {
    textAlign: "center",
  },
  footerText: {
    color: "text.secondary",
  },
  kioskLink: {
    fontSize: "0.8rem",
    fontWeight: 700,
    color: "primary.main",
  },
};
