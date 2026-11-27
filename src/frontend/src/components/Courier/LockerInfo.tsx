import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Stack,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import { courierApi, type LockerDetails } from "../../api/courierApi";
import type { Parcel } from "../../types/domain";
import { StatusBadge } from "../StatusBadge";

interface LockerInfoDialogProps {
  parcel: Parcel | null;
  onClose: () => void;
}

const FALLBACK_STATIONS: Record<string, LockerDetails> = {
  "84a16ee9-4133-4b14-b5ee-8d9e2256d6aa": {
    lockerId: "84a16ee9-4133-4b14-b5ee-8d9e2256d6aa",
    name: "Maison du Savoir - Campus Belval",
    address: "2 Avenue de l'Université, 4361 Esch-sur-Alzette",
    openingHours: "08:00 – 22:00",
    operationalStatus: "ONLINE",
  },
};

export function LockerInfoDialog({ parcel, onClose }: LockerInfoDialogProps) {
  const [locker, setLocker] = useState<LockerDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [offlineNote, setOfflineNote] = useState(false);

  useEffect(() => {
    if (!parcel?.preferredLockerId) {
      setLocker(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setOfflineNote(false);

    courierApi
      .getLockerDetails(parcel.preferredLockerId)
      .then((details) => {
        if (!cancelled) setLocker(details);
      })
      .catch(() => {
        if (cancelled) return;
        const fallback = FALLBACK_STATIONS[parcel.preferredLockerId!] ?? {
          lockerId: parcel.preferredLockerId!,
          name: "Assigned Locker Station",
          address: "7 Avenue du Rock’n’Roll, 4361 Esch-sur-Alzette",
          openingHours: "06:00 – 23:00",
          operationalStatus: "ONLINE",
        };
        setLocker(fallback);
        setOfflineNote(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [parcel]);

  if (!parcel) return null;

  return (
    <Dialog open={true} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={styles.title}>
        Assigned Locker &amp; Drop-Off Info
      </DialogTitle>

      <DialogContent dividers sx={styles.content}>
        {loading ? (
          <Box sx={styles.loaderBox}>
            <CircularProgress size={26} />
          </Box>
        ) : (
          <Stack spacing={2}>
            {offlineNote && (
              <Alert severity="info" sx={styles.alert}>
                Showing cached station metadata while offline.
              </Alert>
            )}

            {/* Station Info Box */}
            <Box sx={styles.cardBox}>
              <Stack direction="row" sx={styles.stationHeader}>
                <Typography variant="subtitle1" sx={styles.stationName}>
                  {locker?.name ?? "Locker Station"}
                </Typography>
                {locker && <StatusBadge status={locker.operationalStatus} />}
              </Stack>

              <Typography variant="body2" sx={styles.detailRow}>
                <strong>Address:</strong> {locker?.address ?? "—"}
              </Typography>
              <Typography variant="body2" sx={styles.detailRow}>
                <strong>Opening Hours:</strong> {locker?.openingHours ?? "—"}
              </Typography>
            </Box>

            {/* Terminal Drop-Off Summary */}
            <Box sx={styles.dropoffBox}>
              <Typography variant="caption" sx={styles.dropoffLabel}>
                TERMINAL DROP-OFF CREDENTIALS
              </Typography>
              <Divider sx={styles.divider} />
              <Typography variant="body2" sx={styles.detailRow}>
                <strong>Parcel ID (enter at kiosk):</strong>{" "}
                <Box component="span" sx={styles.monoCode}>
                  {parcel.parcelId}
                </Box>
              </Typography>
              <Typography variant="body2" sx={styles.detailRow}>
                <strong>Reserved Door:</strong>{" "}
                {parcel.compartmentNumber
                  ? `Box #${parcel.compartmentNumber}`
                  : "Pending"}
              </Typography>
              <Typography variant="body2" sx={styles.detailRow}>
                <strong>Parcel Size:</strong> {parcel.sizeCategory}
              </Typography>
            </Box>
          </Stack>
        )}
      </DialogContent>

      <DialogActions sx={styles.actions}>
        <Button variant="contained" onClick={onClose} sx={styles.closeBtn}>
          Close
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
  loaderBox: {
    py: 4,
    display: "flex",
    justifyContent: "center",
  },
  alert: {
    borderRadius: 2,
  },
  cardBox: {
    p: 2,
    borderRadius: 2,
    bgcolor: "#FFFFFF",
    border: "1px solid #E2E8F0",
  },
  stationHeader: {
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 1,
    mb: 1,
  },
  stationName: {
    fontWeight: 800,
    color: "text.primary",
  },
  detailRow: {
    color: "text.secondary",
    mt: 0.5,
  },
  dropoffBox: {
    p: 2,
    borderRadius: 2,
    bgcolor: "#E3F2FD",
    border: "1px solid #BFDBFE",
  },
  dropoffLabel: {
    fontWeight: 800,
    color: "primary.main",
    letterSpacing: 0.6,
  },
  divider: {
    my: 1,
    borderColor: "#BFDBFE",
  },
  monoCode: {
    fontFamily: "monospace",
    fontWeight: 700,
    color: "text.primary",
  },
  actions: {
    px: 3,
    py: 2,
  },
  closeBtn: {
    bgcolor: "primary.main",
    fontWeight: 700,
    borderRadius: 2,
    "&:hover": { bgcolor: "primary.dark" },
  },
};
