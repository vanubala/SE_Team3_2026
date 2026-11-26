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
import {
  adminApi,
  type AdminLockerOverview,
  type StationOccupancy,
} from "../api/adminApi";
import { AdminKpiRow } from "../components/Admin/AdminKpi";
import { CompartmentStatusDialog } from "../components/Admin/CompartmentStatus";
import { LockerBankGrid } from "../components/LockerGrid";
import { StatusBadge } from "../components/StatusBadge";
import {
  ApiError,
  type Compartment,
  type LockerOperationalStatus,
} from "../types/domain";

// Temporary preview station used only when the backend server is unreachable — remove at integration
const PREVIEW_STATION: AdminLockerOverview = {
  lockerId: "84a16ee9-4133-4b14-b5ee-8d9e2256d6aa",
  name: "Maison du Savoir - Belval Campus",
  address: "2 Avenue de l'Université, 4361 Esch-sur-Alzette",
  openingHours: "08:00 – 22:00",
  operationalStatus: "ONLINE",
  occupancy: {
    total: 12,
    available: 7,
    reserved: 2,
    occupied: 2,
    maintenance: 1,
    occupancyRate: 33.3,
    availableBySize: { SMALL: 3, MEDIUM: 2, LARGE: 2 },
  },
  compartments: [
    {
      compartmentId: "c-01",
      compartmentNumber: 1,
      sizeCategory: "SMALL",
      status: "AVAILABLE",
    },
    {
      compartmentId: "c-02",
      compartmentNumber: 2,
      sizeCategory: "SMALL",
      status: "OCCUPIED",
    },
    {
      compartmentId: "c-03",
      compartmentNumber: 3,
      sizeCategory: "SMALL",
      status: "AVAILABLE",
    },
    {
      compartmentId: "c-04",
      compartmentNumber: 4,
      sizeCategory: "SMALL",
      status: "AVAILABLE",
    },
    {
      compartmentId: "c-05",
      compartmentNumber: 5,
      sizeCategory: "MEDIUM",
      status: "AVAILABLE",
    },
    {
      compartmentId: "c-06",
      compartmentNumber: 6,
      sizeCategory: "MEDIUM",
      status: "RESERVED",
    },
    {
      compartmentId: "c-07",
      compartmentNumber: 7,
      sizeCategory: "MEDIUM",
      status: "AVAILABLE",
    },
    {
      compartmentId: "c-08",
      compartmentNumber: 8,
      sizeCategory: "MEDIUM",
      status: "OCCUPIED",
    },
    {
      compartmentId: "c-09",
      compartmentNumber: 9,
      sizeCategory: "LARGE",
      status: "AVAILABLE",
    },
    {
      compartmentId: "c-10",
      compartmentNumber: 10,
      sizeCategory: "LARGE",
      status: "MAINTENANCE",
    },
    {
      compartmentId: "c-11",
      compartmentNumber: 11,
      sizeCategory: "LARGE",
      status: "RESERVED",
    },
    {
      compartmentId: "c-12",
      compartmentNumber: 12,
      sizeCategory: "LARGE",
      status: "AVAILABLE",
    },
  ],
};

function computePreviewOccupancy(
  compartments: Compartment[]
): StationOccupancy {
  const total = compartments.length;
  const available = compartments.filter((c) => c.status === "AVAILABLE").length;
  const reserved = compartments.filter((c) => c.status === "RESERVED").length;
  const occupied = compartments.filter((c) => c.status === "OCCUPIED").length;
  const maintenance = compartments.filter(
    (c) => c.status === "MAINTENANCE"
  ).length;
  const inUse = reserved + occupied;

  return {
    total,
    available,
    reserved,
    occupied,
    maintenance,
    occupancyRate: total ? Math.round((1000 * inUse) / total) / 10 : 0,
    availableBySize: {
      SMALL: compartments.filter(
        (c) => c.status === "AVAILABLE" && c.sizeCategory === "SMALL"
      ).length,
      MEDIUM: compartments.filter(
        (c) => c.status === "AVAILABLE" && c.sizeCategory === "MEDIUM"
      ).length,
      LARGE: compartments.filter(
        (c) => c.status === "AVAILABLE" && c.sizeCategory === "LARGE"
      ).length,
    },
  };
}

export function AdminDashboard() {
  const [stations, setStations] = useState<AdminLockerOverview[]>([]);
  const [selectedLockerId, setSelectedLockerId] = useState<string>("");
  const [isOfflinePreview, setIsOfflinePreview] = useState(false);
  const [loading, setLoading] = useState(true);
  const [stationUpdating, setStationUpdating] = useState(false);

  const [feedback, setFeedback] = useState<{
    severity: "success" | "warning" | "error";
    message: string;
  } | null>(null);

  const [activeCompartment, setActiveCompartment] =
    useState<Compartment | null>(null);
  const [compSubmitting, setCompSubmitting] = useState(false);
  const [compError, setCompError] = useState<string | null>(null);

  const loadStations = useCallback(async () => {
    setLoading(true);
    try {
      const list = await adminApi.getLockersOverview();
      setIsOfflinePreview(false);
      setStations(list);
      if (list.length > 0) {
        setSelectedLockerId((prev) =>
          list.some((s) => s.lockerId === prev) ? prev : list[0].lockerId
        );
      }
    } catch (err) {
      // Fallback to preview station when backend server is unreachable
      if (err instanceof ApiError && err.code === "NETWORK") {
        setIsOfflinePreview(true);
        setStations((prev) => (prev.length > 0 ? prev : [PREVIEW_STATION]));
        setSelectedLockerId((prev) => prev || PREVIEW_STATION.lockerId);
      } else {
        setFeedback({
          severity: "error",
          message:
            err instanceof ApiError
              ? err.message
              : "Unable to load locker stations.",
        });
      }
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

    if (isOfflinePreview && currentStation) {
      // Interactive local state update while previewing offline
      const target = currentStation.compartments.find(
        (c) => c.compartmentId === compartmentId
      );
      const hasParcel =
        target?.status === "RESERVED" || target?.status === "OCCUPIED";

      if (nextStatus === "AVAILABLE" && hasParcel) {
        setCompError(
          `Compartment #${target?.compartmentNumber} still has an active parcel. Resolve it before making it AVAILABLE.`
        );
        setCompSubmitting(false);
        return;
      }

      const updatedComps = currentStation.compartments.map((c) =>
        c.compartmentId === compartmentId ? { ...c, status: nextStatus } : c
      );
      setStations((prev) =>
        prev.map((st) =>
          st.lockerId === currentStation.lockerId
            ? {
                ...st,
                compartments: updatedComps,
                occupancy: computePreviewOccupancy(updatedComps),
              }
            : st
        )
      );
      setActiveCompartment(null);
      setCompSubmitting(false);
      setFeedback({
        severity:
          nextStatus === "MAINTENANCE" && hasParcel ? "warning" : "success",
        message:
          nextStatus === "MAINTENANCE" && hasParcel
            ? "This compartment still has an active parcel. No new parcel can be assigned to it."
            : `Compartment #${
                target?.compartmentNumber ?? ""
              } updated to ${nextStatus}.`,
      });
      return;
    }

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

    if (isOfflinePreview) {
      setStations((prev) =>
        prev.map((st) =>
          st.lockerId === currentStation.lockerId
            ? { ...st, operationalStatus: nextStatus }
            : st
        )
      );
      setFeedback({
        severity: nextStatus === "ONLINE" ? "success" : "warning",
        message: `Station "${currentStation.name}" is now ${nextStatus}.`,
      });
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
