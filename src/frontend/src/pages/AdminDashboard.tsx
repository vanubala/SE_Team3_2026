import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  MenuItem,
  Stack,
  TextField,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import { adminApi, type AdminLockerOverview } from "../api/adminApi";
import { AdminKpiRow } from "../components/Admin/AdminKpi";
import { CompartmentStatusDialog } from "../components/Admin/CompartmentStatus";
import { LockerBankGrid } from "../components/LockerGrid";
import { StatusBadge } from "../components/StatusBadge";
import {
  ApiError,
  type Compartment,
  type LockerOperationalStatus,
} from "../types/domain";

export function AdminDashboard() {
  const [stations, setStations] = useState<AdminLockerOverview[]>([]);
  const [selectedLockerId, setSelectedLockerId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [stationUpdating, setStationUpdating] = useState(false);

  const [feedback, setFeedback] = useState<{
    severity: "success" | "warning" | "error";
    message: string;
  } | null>(null);

  // Selected compartment modal state
  const [activeCompartment, setActiveCompartment] =
    useState<Compartment | null>(null);
  const [compSubmitting, setCompSubmitting] = useState(false);
  const [compError, setCompError] = useState<string | null>(null);

  const loadStations = useCallback(async () => {
    setLoading(true);
    try {
      const list = await adminApi.getLockersOverview();
      setStations(list);
      if (list.length > 0) {
        setSelectedLockerId((prev) =>
          list.some((s) => s.lockerId === prev) ? prev : list[0].lockerId
        );
      }
    } catch (err) {
      setFeedback({
        severity: "error",
        message:
          err instanceof ApiError
            ? err.message
            : "Unable to load locker stations.",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStations();
  }, [loadStations]);

  const currentStation =
    stations.find((s) => s.lockerId === selectedLockerId) ??
    stations[0] ??
    null;

  const handleConfirmCompartmentStatus = async (
    compartmentId: string,
    nextStatus: "AVAILABLE" | "MAINTENANCE"
  ) => {
    setCompSubmitting(true);
    setCompError(null);
    try {
      const res = await adminApi.updateCompartmentStatus(
        compartmentId,
        nextStatus
      );
      setActiveCompartment(null);
      setFeedback({
        severity: res.warning ? "warning" : "success",
        message:
          res.warning ??
          `Compartment #${
            activeCompartment?.compartmentNumber ?? ""
          } updated to ${res.status}.`,
      });
      await loadStations();
    } catch (err) {
      setCompError(
        err instanceof ApiError
          ? err.message
          : "Failed to update compartment status."
      );
    } finally {
      setCompSubmitting(false);
    }
  };

  const handleStationStatusChange = async (
    nextStatus: LockerOperationalStatus
  ) => {
    if (
      !currentStation ||
      currentStation.operationalStatus === nextStatus ||
      stationUpdating
    ) {
      return;
    }
    setStationUpdating(true);
    try {
      const res = await adminApi.updateLockerStatus(
        currentStation.lockerId,
        nextStatus
      );
      setFeedback({
        severity: res.warning ? "warning" : "success",
        message:
          res.warning ??
          `Station "${currentStation.name}" is now ${res.status}.`,
      });
      await loadStations();
    } catch (err) {
      setFeedback({
        severity: "error",
        message:
          err instanceof ApiError
            ? err.message
            : "Failed to update station status.",
      });
    } finally {
      setStationUpdating(false);
    }
  };

  return (
    <Box>
      {/* Top Header + Location Selector (Inspired by StrongPoint Dashboard) */}
      <Stack direction={{ xs: "column", md: "row" }} sx={styles.headerRow}>
        <Box>
          <Typography variant="h4" sx={styles.title}>
            Locker Network Overview
          </Typography>
          <Typography variant="body2" sx={styles.subtitle}>
            Monitor real-time compartment occupancy and manage station
            maintenance states.
          </Typography>
        </Box>

        <Stack direction="row" spacing={1.5} sx={styles.controlsRow}>
          {stations.length > 1 && (
            <TextField
              select
              size="small"
              label="Station"
              value={selectedLockerId}
              onChange={(e) => setSelectedLockerId(e.target.value)}
              sx={styles.stationSelect}
            >
              {stations.map((st) => (
                <MenuItem key={st.lockerId} value={st.lockerId}>
                  {st.name}
                </MenuItem>
              ))}
            </TextField>
          )}

          <Button
            variant="outlined"
            size="medium"
            disabled={loading}
            onClick={loadStations}
            sx={styles.refreshBtn}
          >
            Refresh
          </Button>
        </Stack>
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

      {loading && !currentStation ? (
        <Box sx={styles.loaderBox}>
          <CircularProgress />
        </Box>
      ) : !currentStation ? (
        <Card elevation={0} sx={styles.emptyCard}>
          <Typography variant="body1" sx={styles.subtitle}>
            No locker stations registered yet.
          </Typography>
        </Card>
      ) : (
        <>
          <AdminKpiRow
            occupancy={currentStation.occupancy}
            stationCount={stations.length}
          />

          {/* Main Station Card: Station Metadata + Interactive Physical Locker Bank */}
          <Card elevation={0} sx={styles.stationCard}>
            <CardContent sx={styles.stationCardBody}>
              <Stack
                direction={{ xs: "column", md: "row" }}
                sx={styles.stationTopBar}
              >
                <Box>
                  <Stack
                    direction="row"
                    spacing={1.5}
                    sx={styles.stationTitleRow}
                  >
                    <Typography variant="h6" sx={styles.stationName}>
                      {currentStation.name}
                    </Typography>
                    <StatusBadge status={currentStation.operationalStatus} />
                  </Stack>
                  <Typography variant="body2" sx={styles.stationMeta}>
                    {currentStation.address} • Hours:{" "}
                    {currentStation.openingHours}
                  </Typography>
                </Box>

                {/* Whole-Station Operational Status Switcher (FR_10) */}
                <TextField
                  select
                  size="small"
                  label="Station Operational Status"
                  value={currentStation.operationalStatus}
                  disabled={stationUpdating}
                  onChange={(e) =>
                    handleStationStatusChange(
                      e.target.value as LockerOperationalStatus
                    )
                  }
                  sx={styles.statusSelect}
                >
                  <MenuItem value="ONLINE">ONLINE (In Service)</MenuItem>
                  <MenuItem value="MAINTENANCE">MAINTENANCE (Blocked)</MenuItem>
                  <MenuItem value="OFFLINE">OFFLINE</MenuItem>
                </TextField>
              </Stack>

              <Typography variant="subtitle2" sx={styles.gridInstruction}>
                Click any compartment door below to toggle between Available and
                Maintenance:
              </Typography>

              <LockerBankGrid
                compartments={currentStation.compartments}
                selectedCompartmentId={activeCompartment?.compartmentId ?? null}
                isSelectable={() => true}
                onSelectCompartment={(comp) => {
                  setCompError(null);
                  setActiveCompartment(comp);
                }}
              />
            </CardContent>
          </Card>
        </>
      )}

      <CompartmentStatusDialog
        compartment={activeCompartment}
        submitting={compSubmitting}
        error={compError}
        onClose={() => setActiveCompartment(null)}
        onConfirmStatus={handleConfirmCompartmentStatus}
      />
    </Box>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  headerRow: {
    justifyContent: "space-between",
    alignItems: { xs: "flex-start", md: "center" },
    gap: 2,
    mb: 3.5,
  },
  title: {
    fontWeight: 800,
    color: "text.primary",
  },
  subtitle: {
    color: "text.secondary",
    mt: 0.5,
  },
  controlsRow: {
    alignItems: "center",
  },
  stationSelect: {
    minWidth: 260,
    bgcolor: "#FFFFFF",
  },
  refreshBtn: {
    borderColor: "primary.main",
    color: "primary.main",
    fontWeight: 700,
    borderRadius: 2,
    bgcolor: "#FFFFFF",
  },
  feedbackAlert: {
    mb: 3,
    borderRadius: 2,
  },
  loaderBox: {
    py: 8,
    display: "flex",
    justifyContent: "center",
  },
  emptyCard: {
    p: 5,
    textAlign: "center",
    borderRadius: 3,
    border: "1px solid #E2E8F0",
  },
  stationCard: {
    borderRadius: 3,
    border: "1px solid #E2E8F0",
    bgcolor: "#FFFFFF",
  },
  stationCardBody: {
    p: { xs: 2.5, sm: 3.5 },
  },
  stationTopBar: {
    justifyContent: "space-between",
    alignItems: { xs: "flex-start", md: "center" },
    gap: 2,
    pb: 2.5,
    mb: 2.5,
    borderBottom: "1px solid #E2E8F0",
  },
  stationTitleRow: {
    alignItems: "center",
    flexWrap: "wrap",
    gap: 1,
  },
  stationName: {
    fontWeight: 800,
    color: "text.primary",
  },
  stationMeta: {
    color: "text.secondary",
    mt: 0.5,
  },
  statusSelect: {
    minWidth: 230,
  },
  gridInstruction: {
    fontWeight: 700,
    color: "text.primary",
    mb: 1.5,
  },
};
