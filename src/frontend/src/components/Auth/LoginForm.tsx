import type { SubmitEvent } from "react";
import {
  Alert,
  Box,
  Button,
  Stack,
  TextField,
  type SxProps,
  type Theme,
} from "@mui/material";

interface LoginFormProps {
  email: string;
  password: string;
  loading: boolean;
  error: string | null;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onSubmit: (e: SubmitEvent<HTMLFormElement>) => void;
}

export function LoginForm({
  email,
  password,
  loading,
  error,
  onEmailChange,
  onPasswordChange,
  onSubmit,
}: LoginFormProps) {
  const isDisabled = loading || !email.trim() || !password;

  return (
    <Box component="form" onSubmit={onSubmit} noValidate>
      <Stack spacing={2.5}>
        {error && (
          <Alert severity="error" sx={styles.errorAlert}>
            {error}
          </Alert>
        )}

        <TextField
          fullWidth
          required
          autoFocus
          type="email"
          label="Email Address"
          placeholder="name@company.lu"
          autoComplete="email"
          disabled={loading}
          value={email}
          onChange={(e) => onEmailChange(e.target.value)}
        />

        <TextField
          fullWidth
          required
          type="password"
          label="Password"
          placeholder="••••••••"
          autoComplete="current-password"
          disabled={loading}
          value={password}
          onChange={(e) => onPasswordChange(e.target.value)}
        />

        <Button
          type="submit"
          fullWidth
          variant="contained"
          size="large"
          disabled={isDisabled}
          sx={styles.submitButton}
        >
          {loading ? "Signing in..." : "Sign In"}
        </Button>
      </Stack>
    </Box>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  errorAlert: {
    borderRadius: 2,
  },
  submitButton: {
    py: 1.4,
    fontSize: "1rem",
    fontWeight: 700,
    borderRadius: 2,
    bgcolor: "primary.main",
    "&:hover": {
      bgcolor: "primary.dark",
    },
  },
};
