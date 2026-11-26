import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import type { Compartment } from "../../types/domain";
import { StatusBadge } from "../StatusBadge";

interface CompartmentStatusDialogProps {
  compartment: Compartment | null;
  submitting: boolean;
  error: string | null;
  onClose: () => void;
  onConfirmStatus: (
    compartmentId: string,
    nextStatus: "AVAILABLE" | "MAINTENANCE"
  ) => Promise<void>;
}

export function CompartmentStatusDialog({
  compartment,
  submitting,
  error,
  onClose,
  onConfirmStatus,
}: CompartmentStatusDialogProps) {
  if (!compartment) return null;

  const isMaintenance = compartment.status === "MAINTENANCE";
  const nextStatus: "AVAILABLE" | "MAINTENANCE" = isMaintenance
    ? "AVAILABLE"
    : "MAINTENANCE";
  const hasParcelRisk =
    compartment.status === "RESERVED" || compartment.status === "OCCUPIED";

  return (
    <Dialog open={true} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={styles.title}>
        Manage Compartment #{compartment.compartmentNumber}
      </DialogTitle>

      <DialogContent dividers sx={styles.content}>
        <Stack direction="row" spacing={1.5} sx={styles.metaRow}>
          <Chip
            size="small"
            label={`Size: ${compartment.sizeCategory}`}
            sx={styles.sizeChip}
          />
          <StatusBadge status={compartment.status} />
        </Stack>

        {error && (
          <Alert severity="error" sx={styles.alert}>
            {error}
          </Alert>
        )}

        {!isMaintenance && hasParcelRisk && (
          <Alert severity="warning" sx={styles.alert}>
            This compartment is currently <strong>{compartment.status}</strong>.
            Marking it as <strong>MAINTENANCE</strong> blocks new courier
            assignments while allowing the existing parcel workflow to complete.
          </Alert>
        )}

        <Box sx={styles.infoBox}>
          <Typography variant="body2" sx={styles.infoText}>
            {isMaintenance
              ? "Restore this compartment to operational service so couriers can assign incoming parcels to it again."
              : "Block this compartment from new courier assignments while hardware inspection or repair is performed."}
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
          onClick={() => onConfirmStatus(compartment.compartmentId, nextStatus)}
          sx={isMaintenance ? styles.restoreBtn : styles.maintenanceBtn}
        >
          {submitting
            ? "Updating..."
            : isMaintenance
            ? "Restore to AVAILABLE"
            : "Set to MAINTENANCE"}
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
  metaRow: {
    alignItems: "center",
    mb: 2,
  },
  sizeChip: {
    fontWeight: 700,
    bgcolor: "#E2E8F0",
    color: "text.primary",
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
  restoreBtn: {
    bgcolor: "#16A34A",
    fontWeight: 700,
    borderRadius: 2,
    "&:hover": { bgcolor: "#15803D" },
  },
  maintenanceBtn: {
    bgcolor: "primary.main",
    fontWeight: 700,
    borderRadius: 2,
    "&:hover": { bgcolor: "primary.dark" },
  },
};
