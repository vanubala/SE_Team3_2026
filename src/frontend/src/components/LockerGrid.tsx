import {
  Box,
  Chip,
  Stack,
  Tooltip,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import type { Compartment } from "../types/domain";

interface LockerBankGridProps {
  compartments: Compartment[];
  selectedCompartmentId?: string | null;
  recommendedCompartmentId?: string | null;
  isSelectable?: (compartment: Compartment) => boolean;
  onSelectCompartment?: (compartment: Compartment) => void;
}

const DOOR_PALETTE: Record<
  Compartment["status"],
  { bg: string; border: string; text: string; latch: string }
> = {
  AVAILABLE: {
    bg: "#86EFAC",
    border: "#4ADE80",
    text: "#14532D",
    latch: "#166534",
  },
  RESERVED: {
    bg: "#93C5FD",
    border: "#60A5FA",
    text: "#1E3A8A",
    latch: "#1D4ED8",
  },
  OCCUPIED: {
    bg: "#818CF8",
    border: "#6366F1",
    text: "#FFFFFF",
    latch: "#EEF2FF",
  },
  MAINTENANCE: {
    bg: "#CBD5E1",
    border: "#94A3B8",
    text: "#334155",
    latch: "#475569",
  },
};

const DOOR_HEIGHT_BY_SIZE: Record<Compartment["sizeCategory"], number> = {
  SMALL: 56,
  MEDIUM: 78,
  LARGE: 106,
};

function buildSymmetricWings(compartments: Compartment[]): {
  leftColumns: Compartment[][];
  rightColumns: Compartment[][];
} {
  const sizeOrder: Record<Compartment["sizeCategory"], number> = {
    SMALL: 0,
    MEDIUM: 1,
    LARGE: 2,
  };

  const ordered = [...compartments].sort(
    (a, b) =>
      sizeOrder[a.sizeCategory] - sizeOrder[b.sizeCategory] ||
      a.compartmentNumber - b.compartmentNumber
  );

  const columns: Compartment[][] = [[], [], [], []];

  ordered.forEach((comp, idx) => {
    columns[idx % 4].push(comp);
  });

  const sortedCols = columns.map((col) =>
    col.sort(
      (a, b) =>
        sizeOrder[a.sizeCategory] - sizeOrder[b.sizeCategory] ||
        a.compartmentNumber - b.compartmentNumber
    )
  );

  return {
    leftColumns: sortedCols.slice(0, 2),
    rightColumns: sortedCols.slice(2, 4),
  };
}

export function LockerBankGrid({
  compartments,
  selectedCompartmentId,
  recommendedCompartmentId,
  isSelectable,
  onSelectCompartment,
}: LockerBankGridProps) {
  const { leftColumns, rightColumns } = buildSymmetricWings(compartments);

  const renderColumn = (col: Compartment[], key: string) => (
    <Box key={key} sx={styles.lockerColumn}>
      {col.map((comp) => {
        const palette = DOOR_PALETTE[comp.status];
        const clickable = isSelectable ? isSelectable(comp) : false;
        const isSelected = comp.compartmentId === selectedCompartmentId;
        const isRecommended = comp.compartmentId === recommendedCompartmentId;

        return (
          <Tooltip
            key={comp.compartmentId}
            title={`Door #${comp.compartmentNumber} • ${comp.sizeCategory} • ${
              comp.status
            }${isRecommended ? " (Best Fit)" : ""}`}
          >
            <Box
              role={clickable ? "button" : undefined}
              tabIndex={clickable ? 0 : undefined}
              onClick={() => {
                if (clickable && onSelectCompartment) {
                  onSelectCompartment(comp);
                }
              }}
              onKeyDown={(e) => {
                if (
                  clickable &&
                  onSelectCompartment &&
                  (e.key === "Enter" || e.key === " ")
                ) {
                  e.preventDefault();
                  onSelectCompartment(comp);
                }
              }}
              sx={{
                ...styles.doorPanel,
                height: DOOR_HEIGHT_BY_SIZE[comp.sizeCategory],
                bgcolor: isSelected ? "#0047AB" : palette.bg,
                borderColor: isSelected ? "#002D72" : palette.border,
                color: isSelected ? "#FFFFFF" : palette.text,
                cursor: clickable ? "pointer" : "not-allowed",
                opacity: clickable || !isSelectable ? 1 : 0.72,
                outline: isSelected ? "2px solid #0047AB" : "none",
                outlineOffset: "1px",
                "&:hover": clickable
                  ? {
                      filter: "brightness(0.95)",
                    }
                  : undefined,
              }}
            >
              <Box sx={styles.doorInfo}>
                <Stack direction="row" spacing={0.6} sx={styles.doorTopLine}>
                  <Typography variant="caption" sx={styles.doorNumber}>
                    #{comp.compartmentNumber}
                  </Typography>
                  <Typography variant="caption" sx={styles.doorSizeTag}>
                    {comp.sizeCategory[0]}
                  </Typography>
                </Stack>

                {isRecommended && (
                  <Chip
                    size="small"
                    label="Best Fit"
                    sx={
                      isSelected
                        ? styles.bestFitSelectedChip
                        : styles.bestFitChip
                    }
                  />
                )}
              </Box>

              <Stack spacing={0.5} sx={styles.latchGroup}>
                <Box
                  sx={{
                    ...styles.latchDot,
                    bgcolor: isSelected ? "#FFFFFF" : palette.latch,
                  }}
                />
                <Box
                  sx={{
                    ...styles.latchBar,
                    bgcolor: isSelected ? "#FFFFFF" : palette.latch,
                  }}
                />
              </Stack>
            </Box>
          </Tooltip>
        );
      })}
    </Box>
  );

  return (
    <Box>
      {/* Status Legend */}
      <Stack direction="row" spacing={2.5} sx={styles.legendRow}>
        {[
          { label: "Available", color: "#4ADE80" },
          { label: "Reserved", color: "#60A5FA" },
          { label: "Occupied", color: "#818CF8" },
          { label: "Maintenance", color: "#94A3B8" },
        ].map((item) => (
          <Stack
            key={item.label}
            direction="row"
            spacing={0.75}
            sx={styles.legendItem}
          >
            <Box sx={{ ...styles.legendDot, bgcolor: item.color }} />
            <Typography variant="caption" sx={styles.legendText}>
              {item.label}
            </Typography>
          </Stack>
        ))}
      </Stack>

      {/* Outer Metallic Locker Cabinet */}
      <Box sx={styles.cabinetOuter}>
        <Box sx={styles.cabinetRoof} />

        {/* Symmetric Cabinet Body: Left Wing (2 cols) + Center Kiosk Tower + Right Wing (2 cols) */}
        <Box sx={styles.cabinetBody}>
          <Box sx={styles.wingGrid}>
            {leftColumns.map((col, idx) => renderColumn(col, `left-${idx}`))}
          </Box>

          {/* Center Kiosk Control Tower */}
          <Box sx={styles.kioskTower}>
            <Box sx={styles.kioskBezel}>
              <Box sx={styles.kioskTouchscreen}>
                <Typography variant="caption" sx={styles.kioskBrand}>
                  SPLS
                </Typography>
              </Box>
              <Box sx={styles.scannerWindow} />
              <Box sx={styles.receiptSlot} />
            </Box>
          </Box>

          <Box sx={styles.wingGrid}>
            {rightColumns.map((col, idx) => renderColumn(col, `right-${idx}`))}
          </Box>
        </Box>

        <Box sx={styles.cabinetPlinth} />
      </Box>
    </Box>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  legendRow: {
    flexWrap: "wrap",
    mb: 1.5,
  },
  legendItem: {
    alignItems: "center",
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: "2px",
  },
  legendText: {
    fontWeight: 600,
    color: "text.secondary",
  },
  cabinetOuter: {
    bgcolor: "#E2E8F0",
    borderRadius: 1.5,
    border: "2px solid #CBD5E1",
    overflow: "hidden",
    boxShadow: "inset 0 1px 0 rgba(255,255,255,0.7)",
  },
  cabinetRoof: {
    height: 8,
    bgcolor: "#CBD5E1",
    borderBottom: "1px solid #94A3B8",
  },
  cabinetBody: {
    display: "flex",
    flexDirection: { xs: "column", sm: "row" },
    gap: "4px",
    p: "6px",
    bgcolor: "#CBD5E1",
  },
  wingGrid: {
    flex: 1,
    display: "grid",
    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    gap: "4px",
  },
  lockerColumn: {
    display: "flex",
    flexDirection: "column",
    gap: "3px",
    bgcolor: "#94A3B8",
    p: "2px",
    borderRadius: "3px",
  },
  doorPanel: {
    px: 1.1,
    py: 0.75,
    borderRadius: "2px",
    border: "1px solid",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    transition: "filter 0.12s ease, background-color 0.12s ease",
    userSelect: "none",
  },
  doorInfo: {
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
    gap: 0.4,
  },
  doorTopLine: {
    alignItems: "baseline",
  },
  doorNumber: {
    fontWeight: 800,
    fontSize: "0.8rem",
    lineHeight: 1,
  },
  doorSizeTag: {
    fontWeight: 700,
    fontSize: "0.68rem",
    opacity: 0.85,
  },
  bestFitChip: {
    height: 17,
    fontSize: "0.58rem",
    fontWeight: 800,
    bgcolor: "#0047AB",
    color: "#FFFFFF",
    borderRadius: "3px",
  },
  bestFitSelectedChip: {
    height: 17,
    fontSize: "0.58rem",
    fontWeight: 800,
    bgcolor: "#FFFFFF",
    color: "#0047AB",
    borderRadius: "3px",
  },
  latchGroup: {
    alignItems: "center",
  },
  latchDot: {
    width: 4,
    height: 4,
    borderRadius: "50%",
    opacity: 0.85,
  },
  latchBar: {
    width: 3,
    height: 14,
    borderRadius: "1px",
    opacity: 0.75,
  },
  kioskTower: {
    width: { xs: "100%", sm: 76 },
    bgcolor: "#F1F5F9",
    borderRadius: "3px",
    border: "1px solid #94A3B8",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    p: 1,
  },
  kioskBezel: {
    width: { xs: 96, sm: "100%" },
    bgcolor: "#E2E8F0",
    border: "1px solid #CBD5E1",
    borderRadius: "3px",
    py: 1.5,
    px: 0.75,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 1.25,
  },
  kioskTouchscreen: {
    width: 44,
    height: 62,
    bgcolor: "#0047AB",
    borderRadius: "3px",
    border: "2px solid #1E293B",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: "0 2px 6px rgba(0, 71, 171, 0.3)",
  },
  kioskBrand: {
    color: "#FFFFFF",
    fontWeight: 800,
    fontSize: "0.65rem",
    letterSpacing: 0.8,
  },
  scannerWindow: {
    width: 26,
    height: 10,
    bgcolor: "#1E293B",
    borderRadius: "2px",
  },
  receiptSlot: {
    width: 32,
    height: 3,
    bgcolor: "#64748B",
    borderRadius: "1px",
  },
  cabinetPlinth: {
    height: 10,
    bgcolor: "#64748B",
    borderTop: "1px solid #475569",
  },
};
