import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import type { LockerOperationalStatus } from "../../types/domain";
import { StatusBadge } from "../StatusBadge";

interface StationStatusDialogProps {
  stationName: string;
  currentStatus: LockerOperationalStatus;
  pendingStatus: LockerOperationalStatus | null;
  activeParcelCount: number;
  submitting: boolean;
  onClose: () => void;
  onConfirm: (nextStatus: LockerOperationalStatus) => Promise<void>;
}

export function StationStatusDialog({
  stationName,
  currentStatus,
  pendingStatus,
  activeParcelCount,
  submitting,
  onClose,
  onConfirm,
}: StationStatusDialogProps) {
  if (!pendingStatus) return null;

  const isBlocking = pendingStatus !== "ONLINE";

  return (
    <Dialog open={true} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={styles.title}>Confirm Station Status Change</DialogTitle>

      <DialogContent dividers sx={styles.content}>
        <Typography variant="subtitle1" sx={styles.stationLabel}>
          {stationName}
        </Typography>

        <Stack direction="row" spacing={1.5} sx={styles.transitionRow}>
          <StatusBadge status={currentStatus} />
          <Typography variant="body2" sx={styles.arrow}>
            →
          </Typography>
          <StatusBadge status={pendingStatus} />
        </Stack>

        {isBlocking && activeParcelCount > 0 && (
          <Alert severity="warning" sx={styles.alert}>
            This station currently has <strong>{activeParcelCount}</strong>{" "}
            active parcel(s) in <strong>RESERVED</strong> or{" "}
            <strong>OCCUPIED</strong> compartments. Switching to{" "}
            <strong>{pendingStatus}</strong> blocks new courier assignments
            while existing parcels remain tracked.
          </Alert>
        )}

        <Box sx={styles.infoBox}>
          <Typography variant="body2" sx={styles.infoText}>
            {pendingStatus === "ONLINE"
              ? "Restore this station to normal operation so couriers can assign compartments and deposit parcels."
              : `Are you sure you want to set this station to ${pendingStatus}? Couriers will not be able to assign new parcels to it until it is restored to ONLINE.`}
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions sx={styles.actions}>
        <Button onClick={onClose} disabled={submitting} sx={styles.cancelBtn}>
          Cancel
        </Button>
        <Button
          variant="contained"
          disabled={submitting}
          onClick={() => onConfirm(pendingStatus)}
          sx={isBlocking ? styles.warnConfirmBtn : styles.onlineConfirmBtn}
        >
          {submitting ? "Updating..." : `Confirm ${pendingStatus}`}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  title: {
    fontWeight: 800,
    color: "text.primary",
  },
  content: {
    bgcolor: "#F8FAFC",
    p: 3,
  },
  stationLabel: {
    fontWeight: 700,
    color: "text.primary",
    mb: 1.5,
  },
  transitionRow: {
    alignItems: "center",
    mb: 2,
  },
  arrow: {
    fontWeight: 800,
    color: "text.secondary",
  },
  alert: {
    mb: 2,
    borderRadius: 2,
  },
  infoBox: {
    p: 2,
    borderRadius: 2,
    bgcolor: "#FFFFFF",
    border: "1px solid #E2E8F0",
  },
  infoText: {
    color: "text.secondary",
  },
  actions: {
    px: 3,
    py: 2,
  },
  cancelBtn: {
    color: "text.secondary",
    fontWeight: 700,
  },
  warnConfirmBtn: {
    bgcolor: "#D97706",
    fontWeight: 700,
    borderRadius: 2,
    "&:hover": { bgcolor: "#B45309" },
  },
  onlineConfirmBtn: {
    bgcolor: "primary.main",
    fontWeight: 700,
    borderRadius: 2,
    "&:hover": { bgcolor: "primary.dark" },
  },
};
