import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import { courierApi } from "../../api/courierApi";
import { ApiError, type Compartment, type Parcel } from "../../types/domain";
import { LockerBankGrid } from "../LockerGrid";

interface AssignCompartmentDialogProps {
  parcel: Parcel | null;
  onClose: () => void;
  onAssigned: (parcelId: string, compartmentNumber: number) => void;
}

const STATIONS = [
  {
    id: "84a16ee9-4133-4b14-b5ee-8d9e2256d6aa",
    name: "Belval Plaza Station — Esch-sur-Alzette",
  },
];

export function AssignCompartmentDialog({
  parcel,
  onClose,
  onAssigned,
}: AssignCompartmentDialogProps) {
  const [lockerId, setLockerId] = useState(STATIONS[0].id);
  const [compartments, setCompartments] = useState<Compartment[]>([]);
  const [recommendedId, setRecommendedId] = useState<string | null>(null);
  const [selectedCompId, setSelectedCompId] = useState<string>("");
  const [loadingOptions, setLoadingOptions] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!parcel) return;
    setLockerId(parcel.preferredLockerId || STATIONS[0].id);
  }, [parcel]);

  useEffect(() => {
    if (!parcel || !lockerId) return;

    let cancelled = false;
    setLoadingOptions(true);
    setError(null);
    setCompartments([]);
    setSelectedCompId("");

    courierApi
      .getAvailableCompartments(lockerId, parcel.sizeCategory)
      .then((res) => {
        if (cancelled) return;
        setCompartments(res.availableCompartments);
        setRecommendedId(res.recommendedCompartmentId);
        setSelectedCompId(res.recommendedCompartmentId);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load available compartments."
        );
      })
      .finally(() => {
        if (!cancelled) setLoadingOptions(false);
      });

    return () => {
      cancelled = true;
    };
  }, [parcel, lockerId]);

  const handleConfirm = async () => {
    if (!parcel || !selectedCompId || submitting) return;
    setSubmitting(true);
    setError(null);

    try {
      const res = await courierApi.assignCompartment(
        parcel.parcelId,
        lockerId,
        selectedCompId
      );
      onAssigned(res.parcelId, res.compartmentNumber);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to assign compartment."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={parcel !== null} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={styles.dialogTitle}>
        Assign Locker Compartment — {parcel?.trackingNumber}
      </DialogTitle>

      <DialogContent dividers sx={styles.dialogContent}>
        <Stack direction="row" spacing={1.5} sx={styles.parcelMetaRow}>
          <Chip
            size="small"
            label={`Parcel Size: ${parcel?.sizeCategory}`}
            sx={styles.metaChip}
          />
          <Typography variant="caption" sx={styles.metaText}>
            Recipient: {parcel?.recipientContact}
          </Typography>
        </Stack>

        <TextField
          select
          fullWidth
          label="Target Locker Station"
          value={lockerId}
          disabled={loadingOptions || submitting}
          onChange={(e) => setLockerId(e.target.value)}
          sx={styles.stationSelect}
        >
          {STATIONS.map((st) => (
            <MenuItem key={st.id} value={st.id}>
              {st.name}
            </MenuItem>
          ))}
        </TextField>

        {error && (
          <Alert severity="error" sx={styles.alert}>
            {error}
          </Alert>
        )}

        {loadingOptions ? (
          <Box sx={styles.loaderBox}>
            <CircularProgress size={28} />
          </Box>
        ) : (
          compartments.length > 0 && (
            <Box>
              <Typography variant="subtitle2" sx={styles.gridLabel}>
                Click an available compartment door to reserve it:
              </Typography>

              <LockerBankGrid
                compartments={compartments}
                selectedCompartmentId={selectedCompId}
                recommendedCompartmentId={recommendedId}
                isSelectable={(comp) => comp.status === "AVAILABLE"}
                onSelectCompartment={(comp) =>
                  setSelectedCompId(comp.compartmentId)
                }
              />
            </Box>
          )
        )}
      </DialogContent>

      <DialogActions sx={styles.dialogActions}>
        <Button onClick={onClose} disabled={submitting} sx={styles.cancelBtn}>
          Cancel
        </Button>
        <Button
          variant="contained"
          disabled={submitting || loadingOptions || !selectedCompId}
          onClick={handleConfirm}
          sx={styles.confirmBtn}
        >
          {submitting ? "Assigning..." : "Confirm Assignment"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  dialogTitle: {
    fontWeight: 800,
    color: "text.primary",
  },
  dialogContent: {
    bgcolor: "#F8FAFC",
    p: 3,
  },
  parcelMetaRow: {
    alignItems: "center",
    mb: 2.5,
  },
  metaChip: {
    bgcolor: "#E3F2FD",
    color: "primary.main",
    fontWeight: 700,
  },
  metaText: {
    color: "text.secondary",
  },
  stationSelect: {
    bgcolor: "#FFFFFF",
    mb: 2.5,
  },
  alert: {
    mb: 2,
    borderRadius: 2,
  },
  loaderBox: {
    py: 4,
    display: "flex",
    justifyContent: "center",
  },
  gridLabel: {
    fontWeight: 700,
    color: "text.primary",
    mb: 1,
  },
  dialogActions: {
    px: 3,
    py: 2,
  },
  cancelBtn: {
    color: "text.secondary",
    fontWeight: 700,
  },
  confirmBtn: {
    bgcolor: "primary.main",
    fontWeight: 700,
    px: 3,
    borderRadius: 2,
    "&:hover": { bgcolor: "primary.dark" },
  },
};
