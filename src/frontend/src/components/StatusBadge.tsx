import { Chip, type SxProps, type Theme } from "@mui/material";
import type {
  CompartmentStatus,
  LockerOperationalStatus,
  ParcelStatus,
} from "../types/domain";

type AnyStatus = ParcelStatus | CompartmentStatus | LockerOperationalStatus;

interface StatusBadgeProps {
  status: AnyStatus;
}

const BADGE_CONFIG: Record<
  AnyStatus,
  { label: string; bg: string; color: string }
> = {
  REGISTERED: { label: "Registered", bg: "#E3F2FD", color: "#0047AB" },
  ASSIGNED: { label: "Assigned", bg: "#DBEAFE", color: "#1E40AF" },
  READY_FOR_PICKUP: {
    label: "Ready for Pickup",
    bg: "#DCFCE7",
    color: "#166534",
  },
  COLLECTED: { label: "Collected", bg: "#F1F5F9", color: "#475569" },
  EXPIRED: { label: "Expired", bg: "#FEE2E2", color: "#991B1B" },
  AVAILABLE: { label: "Available", bg: "#DCFCE7", color: "#166534" },
  RESERVED: { label: "Reserved", bg: "#E3F2FD", color: "#0047AB" },
  OCCUPIED: { label: "Occupied", bg: "#FEF3C7", color: "#92400E" },
  MAINTENANCE: { label: "Maintenance", bg: "#FEE2E2", color: "#991B1B" },
  ONLINE: { label: "Online", bg: "#DCFCE7", color: "#166534" },
  OFFLINE: { label: "Offline", bg: "#FEE2E2", color: "#991B1B" },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const cfg = BADGE_CONFIG[status] ?? {
    label: status,
    bg: "#F1F5F9",
    color: "#334155",
  };

  return (
    <Chip
      size="small"
      label={cfg.label}
      sx={{ ...styles.chip, bgcolor: cfg.bg, color: cfg.color }}
    />
  );
}

const styles: Record<string, SxProps<Theme>> = {
  chip: {
    fontWeight: 700,
    fontSize: "0.75rem",
    borderRadius: 1.5,
  },
};
