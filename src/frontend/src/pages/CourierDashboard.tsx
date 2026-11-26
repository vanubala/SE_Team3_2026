import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Stack,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import { courierApi, type RegisterParcelInput } from "../api/courierApi";
import { AssignCompartmentDialog } from "../components/Courier/AssignCompartment";
import { CourierStatsRow } from "../components/Courier/CourierStats";
import { ParcelListTable } from "../components/Courier/ParcelList";
import { RegisterParcelDialog } from "../components/Courier/RegisterForm";
import { useAuth } from "../context/AuthContext";
import { ApiError, type Parcel } from "../types/domain";

export function CourierDashboard() {
  const { user } = useAuth();

  const [parcels, setParcels] = useState<Parcel[]>([]);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState<{
    severity: "success" | "error";
    message: string;
  } | null>(null);

  // UC1 Registration dialog state
  const [registerOpen, setRegisterOpen] = useState(false);
  const [registerSubmitting, setRegisterSubmitting] = useState(false);
  const [registerError, setRegisterError] = useState<string | null>(null);

  // UC2 Compartment Assignment dialog state
  const [parcelToAssign, setParcelToAssign] = useState<Parcel | null>(null);

  const loadParcels = useCallback(async () => {
    setLoading(true);
    try {
      const list = await courierApi.listParcels();
      setParcels(list);
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.message
          : "Failed to load courier parcels.";
      setFeedback({ severity: "error", message: msg });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadParcels();
  }, [loadParcels]);

  const handleRegisterParcel = async (input: RegisterParcelInput) => {
    setRegisterSubmitting(true);
    setRegisterError(null);
    try {
      const created = await courierApi.registerParcel(input);
      setRegisterOpen(false);
      setFeedback({
        severity: "success",
        message: `Parcel ${created.trackingNumber} registered (Terminal ID: ${created.parcelId}).`,
      });
      await loadParcels();
    } catch (err) {
      setRegisterError(
        err instanceof ApiError ? err.message : "Unable to register parcel."
      );
    } finally {
      setRegisterSubmitting(false);
    }
  };

  const handleCompartmentAssigned = async (
    parcelId: string,
    compartmentNumber: number
  ) => {
    setParcelToAssign(null);
    setFeedback({
      severity: "success",
      message: `Parcel ${parcelId} assigned to Compartment #${compartmentNumber}. Ready for terminal drop-off.`,
    });
    await loadParcels();
  };

  const filteredParcels =
    statusFilter === "ALL"
      ? parcels
      : parcels.filter((p) => p.status === statusFilter);

  return (
    <Box>
      <Stack direction={{ xs: "column", sm: "row" }} sx={styles.headerRow}>
        <Box>
          <Typography variant="h4" sx={styles.greeting}>
            Hi, {user?.name ?? "Courier"}
          </Typography>
        </Box>

        <Button
          variant="contained"
          size="large"
          onClick={() => {
            setRegisterError(null);
            setRegisterOpen(true);
          }}
          sx={styles.registerCtaBtn}
        >
          + Register Parcel
        </Button>
      </Stack>

      {feedback && (
        <Alert
          severity={feedback.severity}
          onClose={() => setFeedback(null)}
          sx={styles.feedbackAlert}
        >
          {feedback.message}
        </Alert>
      )}

      <CourierStatsRow parcels={parcels} />

      <ParcelListTable
        parcels={filteredParcels}
        statusFilter={statusFilter}
        loading={loading}
        onFilterChange={setStatusFilter}
        onOpenAssign={setParcelToAssign}
      />

      <RegisterParcelDialog
        open={registerOpen}
        submitting={registerSubmitting}
        error={registerError}
        onClose={() => setRegisterOpen(false)}
        onSubmit={handleRegisterParcel}
      />

      <AssignCompartmentDialog
        parcel={parcelToAssign}
        onClose={() => setParcelToAssign(null)}
        onAssigned={handleCompartmentAssigned}
      />
    </Box>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  headerRow: {
    justifyContent: "space-between",
    alignItems: { xs: "flex-start", sm: "center" },
    gap: 2,
    mb: 3.5,
  },
  greeting: {
    fontWeight: 800,
    color: "text.primary",
  },
  subtitle: {
    color: "text.secondary",
    mt: 0.5,
  },
  registerCtaBtn: {
    bgcolor: "primary.main",
    fontWeight: 700,
    px: 3,
    py: 1.25,
    borderRadius: 2,
    "&:hover": { bgcolor: "primary.dark" },
  },
  feedbackAlert: {
    mb: 3,
    borderRadius: 2,
  },
};
