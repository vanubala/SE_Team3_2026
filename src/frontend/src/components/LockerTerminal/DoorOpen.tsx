import {
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Stack,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import type { TerminalMode } from "../../types/terminal";

interface DoorOpenStepProps {
  mode: TerminalMode;
  compartmentNumber: number;
  parcelId: string;
  loading: boolean;
  onConfirmClose: () => void;
}

export function DoorOpenStep({
  mode,
  compartmentNumber,
  parcelId,
  loading,
  onConfirmClose,
}: DoorOpenStepProps) {
  const isPickup = mode === "PICKUP";

  return (
    <Box>
      <Typography variant="h5" sx={styles.heading}>
        {isPickup ? "Customer Pickup" : "Courier Deposit"}
      </Typography>

      <Divider sx={styles.divider} />

      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={4}
        sx={styles.contentRow}
      >
        <Card elevation={3} sx={styles.lockerCard}>
          <Box sx={styles.lockerBanner}>
            <Typography variant="subtitle1" sx={styles.lockerLabel}>
              LOCKER
            </Typography>
          </Box>
          <CardContent sx={styles.lockerNumberBox}>
            <Typography variant="h1" sx={styles.lockerNumber}>
              {compartmentNumber}
            </Typography>
          </CardContent>
        </Card>

        <Box sx={styles.instructionColumn}>
          <Typography variant="h6" sx={styles.instructionText}>
            {isPickup
              ? "Please collect your parcel and remember to close the locker door."
              : `Place parcel ${parcelId} inside and remember to close the locker door.`}
          </Typography>

          <Button
            variant="contained"
            color="success"
            size="large"
            fullWidth
            disabled={loading}
            onClick={onConfirmClose}
            sx={styles.confirmButton}
          >
            {loading ? "Confirming..." : "Simulate Closing Door"}
          </Button>
        </Box>
      </Stack>
    </Box>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  heading: {
    fontWeight: 700,
    textAlign: "center",
    color: "#334155",
    mb: 3,
  },
  divider: {
    mb: 4,
  },
  contentRow: {
    alignItems: "center",
    justifyContent: "center",
  },
  lockerCard: {
    width: 220,
    textAlign: "center",
    borderRadius: 2,
    overflow: "hidden",
    border: "1px solid #e2e8f0",
  },
  lockerBanner: {
    bgcolor: "#ea580c",
    color: "#fff",
    py: 1,
  },
  lockerLabel: {
    fontWeight: 800,
    letterSpacing: 1.5,
  },
  lockerNumberBox: {
    py: 4,
    bgcolor: "#f8fafc",
  },
  lockerNumber: {
    fontWeight: 800,
    color: "#0f172a",
  },
  instructionColumn: {
    maxWidth: 280,
    textAlign: { xs: "center", sm: "left" },
  },
  instructionText: {
    fontWeight: 600,
    color: "#1e293b",
    mb: 1,
  },
  confirmButton: {
    mt: 2,
    py: 1.5,
    fontWeight: 700,
    borderRadius: 2,
    textTransform: "none",
  },
};
