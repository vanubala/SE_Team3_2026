import {
  Box,
  Button,
  Card,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import type { Parcel } from "../../types/domain";
import { StatusBadge } from "../StatusBadge";

interface ParcelListTableProps {
  parcels: Parcel[];
  statusFilter: string;
  loading: boolean;
  onFilterChange: (status: string) => void;
  onOpenAssign: (parcel: Parcel) => void;
  onViewLockerInfo: (parcel: Parcel) => void;
}

const FILTERS = [
  { value: "ALL", label: "All" },
  { value: "REGISTERED", label: "Registered" },
  { value: "ASSIGNED", label: "Assigned" },
  { value: "READY_FOR_PICKUP", label: "Ready for Pickup" },
  { value: "COLLECTED", label: "Collected" },
];

const LOCKER_NAMES: Record<string, string> = {
  "84a16ee9-4133-4b14-b5ee-8d9e2256d6aa": "Maison du Savoir — Belval Campus",
};

function formatDeliveryDate(iso?: string): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ParcelListTable({
  parcels,
  statusFilter,
  loading,
  onFilterChange,
  onOpenAssign,
  onViewLockerInfo,
}: ParcelListTableProps) {
  return (
    <Card elevation={0} sx={styles.tableCard}>
      <Box sx={styles.toolbar}>
        <Typography variant="h6" sx={styles.sectionTitle}>
          Parcel Queue &amp; Deliveries
        </Typography>

        <ToggleButtonGroup
          size="small"
          exclusive
          value={statusFilter}
          onChange={(_, next) => {
            if (next) onFilterChange(next);
          }}
          sx={styles.filterGroup}
        >
          {FILTERS.map((f) => (
            <ToggleButton key={f.value} value={f.value} sx={styles.filterBtn}>
              {f.label}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Box>

      <TableContainer>
        <Table>
          <TableHead sx={styles.tableHead}>
            <TableRow>
              <TableCell sx={styles.headCell}>Parcel ID</TableCell>
              <TableCell sx={styles.headCell}>Delivery Location</TableCell>
              <TableCell sx={styles.headCell}>Size</TableCell>
              <TableCell sx={styles.headCell}>Expected Delivery</TableCell>
              <TableCell sx={styles.headCell}>Instructions</TableCell>
              <TableCell sx={styles.headCell}>Status</TableCell>
              <TableCell sx={styles.headCell}>Compartment</TableCell>
              <TableCell align="right" sx={styles.headCell}>
                Action
              </TableCell>
            </TableRow>
          </TableHead>

          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} sx={styles.emptyCell}>
                  Loading parcels...
                </TableCell>
              </TableRow>
            ) : parcels.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} sx={styles.emptyCell}>
                  No parcels found. Click on &ldquo;Register Parcel&rdquo; to
                  add one.
                </TableCell>
              </TableRow>
            ) : (
              parcels.map((parcel) => {
                const locationLabel = parcel.preferredLockerId
                  ? LOCKER_NAMES[parcel.preferredLockerId] ??
                    parcel.preferredLockerId
                  : "Unassigned station";

                return (
                  <TableRow key={parcel.parcelId} hover>
                    <TableCell sx={styles.monoCell}>
                      {parcel.parcelId}
                    </TableCell>
                    <TableCell sx={styles.locationCell}>
                      {locationLabel}
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={parcel.sizeCategory}
                        sx={styles.sizeChip}
                      />
                    </TableCell>
                    <TableCell sx={styles.dateCell}>
                      {formatDeliveryDate(parcel.expectedDelivery)}
                    </TableCell>
                    <TableCell sx={styles.notesCell}>
                      {parcel.notes || "—"}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={parcel.status} />
                    </TableCell>
                    <TableCell>
                      {parcel.compartmentNumber ? (
                        <Typography variant="body2" sx={styles.boxLabel}>
                          Box #{parcel.compartmentNumber}
                        </Typography>
                      ) : (
                        <Typography variant="caption" sx={styles.mutedText}>
                          Not assigned
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      {parcel.status === "REGISTERED" ? (
                        <Button
                          variant="contained"
                          size="small"
                          onClick={() => onOpenAssign(parcel)}
                          sx={styles.assignBtn}
                        >
                          Assign Locker
                        </Button>
                      ) : (
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => onViewLockerInfo(parcel)}
                          sx={styles.infoBtn}
                        >
                          Locker Info
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Card>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  tableCard: {
    borderRadius: 3,
    border: "1px solid #E2E8F0",
    bgcolor: "#FFFFFF",
    overflow: "hidden",
  },
  toolbar: {
    px: 3,
    py: 2,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: 2,
    borderBottom: "1px solid #E2E8F0",
  },
  sectionTitle: {
    fontWeight: 800,
    color: "text.primary",
  },
  filterGroup: {
    bgcolor: "#F8FAFC",
  },
  filterBtn: {
    px: 1.5,
    py: 0.5,
    fontSize: "0.75rem",
    fontWeight: 700,
    "&.Mui-selected": {
      bgcolor: "primary.main",
      color: "#FFFFFF",
      "&:hover": { bgcolor: "primary.dark" },
    },
  },
  tableHead: {
    bgcolor: "#F8FAFC",
  },
  headCell: {
    fontWeight: 700,
    color: "text.secondary",
    fontSize: "0.78rem",
  },
  monoCell: {
    fontFamily: "monospace",
    fontSize: "0.8rem",
    fontWeight: 600,
    color: "text.primary",
  },
  locationCell: {
    fontWeight: 600,
    color: "text.primary",
  },
  dateCell: {
    whiteSpace: "nowrap",
    color: "text.secondary",
    fontSize: "0.84rem",
  },
  notesCell: {
    maxWidth: 220,
    color: "text.secondary",
    fontSize: "0.84rem",
  },
  sizeChip: {
    fontWeight: 700,
    bgcolor: "#F1F5F9",
    color: "text.primary",
  },
  boxLabel: {
    fontWeight: 700,
    color: "primary.main",
  },
  mutedText: {
    color: "text.secondary",
  },
  assignBtn: {
    bgcolor: "primary.main",
    fontWeight: 700,
    borderRadius: 1.5,
    "&:hover": { bgcolor: "primary.dark" },
  },
  infoBtn: {
    borderColor: "primary.main",
    color: "primary.main",
    fontWeight: 700,
    borderRadius: 1.5,
    "&:hover": { bgcolor: "#E3F2FD" },
  },
  emptyCell: {
    py: 5,
    textAlign: "center",
    color: "text.secondary",
  },
};
