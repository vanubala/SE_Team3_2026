import type { SubmitEvent } from "react";
import {
  Box,
  Button,
  Paper,
  Stack,
  TextField,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import type { TerminalMode } from "../../types/terminal";

interface CodeEntryStepProps {
  mode: TerminalMode;
  code: string;
  loading: boolean;
  isLocked: boolean;
  onCodeChange: (value: string) => void;
  onSubmit: (e: SubmitEvent<HTMLFormElement>) => void;
  onBack: () => void;
}

export function CodeEntryStep({
  mode,
  code,
  loading,
  isLocked,
  onCodeChange,
  onSubmit,
  onBack,
}: CodeEntryStepProps) {
  const isPickup = mode === "PICKUP";
  const isDisabled =
    loading ||
    (isPickup && (isLocked || code.length < 6)) ||
    (!isPickup && !code.trim());

  const steps = [
    {
      number: "1",
      label: isPickup ? "Enter 6-Digit PIN" : "Enter Parcel ID",
      color: "#2563eb",
    },
    { number: "2", label: "Compartment Opens", color: "#2563eb" },
    {
      number: "3",
      label: isPickup ? "Collect & Close Door" : "Place & Close Door",
      color: "#2e7d32",
    },
  ];

  return (
    <Box>
      <Button onClick={onBack} sx={styles.backButton}>
        ← Back to Action Selection
      </Button>

      <Typography variant="h4" sx={styles.heading}>
        {isPickup ? "Pick Up Your Package" : "Drop Off a Package"}
      </Typography>

      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        sx={styles.stepsRow}
      >
        {steps.map((step) => (
          <Paper key={step.number} variant="outlined" sx={styles.stepCard}>
            <Box sx={{ ...styles.stepBadge, bgcolor: step.color }}>
              {step.number}
            </Box>
            <Typography variant="body2" sx={styles.stepText}>
              {step.label}
            </Typography>
          </Paper>
        ))}
      </Stack>

      <Box component="form" onSubmit={onSubmit} sx={styles.formWrapper}>
        <TextField
          fullWidth
          autoFocus
          label={isPickup ? "6-Digit Pickup PIN" : "Assigned Parcel ID"}
          placeholder={isPickup ? "e.g. 482910" : "e.g. p-7a8b9c0d"}
          disabled={loading || (isPickup && isLocked)}
          value={code}
          onChange={(e) =>
            onCodeChange(
              isPickup
                ? e.target.value.replace(/\D/g, "").slice(0, 6)
                : e.target.value
            )
          }
          slotProps={{
            htmlInput: {
              style: {
                textAlign: "center",
                fontSize: "1.4rem",
                fontWeight: 700,
                letterSpacing: isPickup ? "0.25em" : "normal",
              },
            },
          }}
          sx={styles.codeInput}
        />

        <Button
          type="submit"
          fullWidth
          variant="contained"
          size="large"
          color={isPickup ? "success" : "primary"}
          disabled={isDisabled}
          sx={styles.submitButton}
        >
          {isPickup && isLocked
            ? "Terminal Locked (15m)"
            : loading
            ? "Verifying..."
            : "Open Locker"}
        </Button>
      </Box>
    </Box>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  backButton: {
    mb: 2,
    textTransform: "none",
    fontWeight: 600,
  },
  heading: {
    fontWeight: 800,
    textAlign: "center",
    color: "#1e293b",
    mb: 3,
  },
  stepsRow: {
    mb: 4,
  },
  stepCard: {
    flex: 1,
    p: 2,
    textAlign: "center",
    borderRadius: 2,
    bgcolor: "#f8fafc",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 1,
  },
  stepBadge: {
    width: 34,
    height: 34,
    borderRadius: "50%",
    color: "#ffffff",
    fontWeight: 800,
    fontSize: "1rem",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  stepText: {
    fontWeight: 600,
  },
  formWrapper: {
    maxWidth: 420,
    mx: "auto",
  },
  codeInput: {
    mb: 2.5,
  },
  submitButton: {
    py: 1.5,
    fontSize: "1.1rem",
    fontWeight: 700,
    borderRadius: 2,
    textTransform: "none",
  },
};
