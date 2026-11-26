import { useState, type SubmitEvent } from "react";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  MenuItem,
  Stack,
  TextField,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import type { RegisterParcelInput } from "../../api/courierApi";
import type { SizeCategory } from "../../types/domain";

interface RegisterParcelDialogProps {
  open: boolean;
  submitting: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (payload: RegisterParcelInput) => Promise<void>;
}

const KNOWN_LOCKERS = [
  { id: "", label: "No preferred station (choose during assignment)" },
  {
    id: "84a16ee9-4133-4b14-b5ee-8d9e2256d6aa",
    label: "Maison du Savoir — Belval Campus",
  },
];

export function RegisterParcelDialog({
  open,
  submitting,
  error,
  onClose,
  onSubmit,
}: RegisterParcelDialogProps) {
  const defaultDelivery = new Date(Date.now() + 24 * 3600_000)
    .toISOString()
    .slice(0, 16);

  const [trackingNumber, setTrackingNumber] = useState("");
  const [sizeCategory, setSizeCategory] = useState<SizeCategory>("MEDIUM");
  const [recipientContact, setRecipientContact] = useState("");
  const [expectedDelivery, setExpectedDelivery] = useState(defaultDelivery);
  const [preferredLockerId, setPreferredLockerId] = useState("");
  const [notes, setNotes] = useState("");

  const handleFormSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (
      !trackingNumber.trim() ||
      !recipientContact.trim() ||
      !expectedDelivery ||
      submitting
    )
      return;

    await onSubmit({
      trackingNumber,
      sizeCategory,
      recipientContact,
      expectedDelivery,
      preferredLockerId: preferredLockerId || undefined,
      notes: notes || undefined,
    });

    setTrackingNumber("");
    setRecipientContact("");
    setNotes("");
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <Box component="form" onSubmit={handleFormSubmit}>
        <DialogTitle sx={styles.dialogTitle}>
          Register Incoming Parcel
        </DialogTitle>

        <DialogContent dividers sx={styles.dialogContent}>
          {error && (
            <Alert severity="error" sx={styles.alert}>
              {error}
            </Alert>
          )}

          {/* Two-column layout inspired by Image 2 (Shipment Details + Package Characteristics) */}
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Box sx={styles.panelBox}>
                <Typography variant="subtitle1" sx={styles.panelHeading}>
                  Shipment &amp; Recipient
                </Typography>

                <Stack spacing={2.25}>
                  <TextField
                    required
                    fullWidth
                    autoFocus
                    label="Barcode / Tracking Number"
                    placeholder="e.g. LU-2026-88412"
                    disabled={submitting}
                    value={trackingNumber}
                    onChange={(e) => setTrackingNumber(e.target.value)}
                  />

                  <TextField
                    required
                    fullWidth
                    label="Recipient Contact (Email or Phone)"
                    placeholder="recipient@example.lu or +352621000111"
                    disabled={submitting}
                    value={recipientContact}
                    onChange={(e) => setRecipientContact(e.target.value)}
                  />

                  <TextField
                    select
                    fullWidth
                    label="Preferred Locker Station (Optional)"
                    disabled={submitting}
                    value={preferredLockerId}
                    onChange={(e) => setPreferredLockerId(e.target.value)}
                  >
                    {KNOWN_LOCKERS.map((loc) => (
                      <MenuItem key={loc.id} value={loc.id}>
                        {loc.label}
                      </MenuItem>
                    ))}
                  </TextField>
                </Stack>
              </Box>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Box sx={styles.panelBox}>
                <Typography variant="subtitle1" sx={styles.panelHeading}>
                  Package Characteristics
                </Typography>

                <Stack spacing={2.25}>
                  <TextField
                    select
                    required
                    fullWidth
                    label="Package Size Category"
                    disabled={submitting}
                    value={sizeCategory}
                    onChange={(e) =>
                      setSizeCategory(e.target.value as SizeCategory)
                    }
                  >
                    <MenuItem value="SMALL">
                      SMALL (Letters, small boxes)
                    </MenuItem>
                    <MenuItem value="MEDIUM">
                      MEDIUM (Standard shoebox / apparel)
                    </MenuItem>
                    <MenuItem value="LARGE">LARGE (Oversized parcel)</MenuItem>
                  </TextField>

                  <TextField
                    required
                    fullWidth
                    type="datetime-local"
                    label="Expected Delivery Date & Time"
                    slotProps={{ inputLabel: { shrink: true } }}
                    disabled={submitting}
                    value={expectedDelivery}
                    onChange={(e) => setExpectedDelivery(e.target.value)}
                  />

                  <TextField
                    fullWidth
                    multiline
                    rows={2}
                    label="Delivery Notes (Optional)"
                    placeholder="e.g. Fragile, handle with care"
                    disabled={submitting}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                  />
                </Stack>
              </Box>
            </Grid>
          </Grid>
        </DialogContent>

        <DialogActions sx={styles.dialogActions}>
          <Button onClick={onClose} disabled={submitting} sx={styles.cancelBtn}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={
              submitting || !trackingNumber.trim() || !recipientContact.trim()
            }
            sx={styles.submitBtn}
          >
            {submitting ? "Registering..." : "Register Parcel"}
          </Button>
        </DialogActions>
      </Box>
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
  alert: {
    mb: 2.5,
    borderRadius: 2,
  },
  panelBox: {
    bgcolor: "#FFFFFF",
    p: 2.5,
    borderRadius: 2.5,
    border: "1px solid #E2E8F0",
    height: "100%",
  },
  panelHeading: {
    fontWeight: 800,
    color: "primary.main",
    mb: 2,
  },
  dialogActions: {
    px: 3,
    py: 2,
  },
  cancelBtn: {
    color: "text.secondary",
    fontWeight: 700,
  },
  submitBtn: {
    bgcolor: "primary.main",
    fontWeight: 700,
    px: 3,
    borderRadius: 2,
    "&:hover": { bgcolor: "primary.dark" },
  },
};
