import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import type { StationOccupancy } from "../../api/adminApi";

interface AdminKpiRowProps {
  occupancy: StationOccupancy;
  stationCount: number;
}

export function AdminKpiRow({ occupancy, stationCount }: AdminKpiRowProps) {
  const inUse = occupancy.reserved + occupancy.occupied;
  const { SMALL, MEDIUM, LARGE } = occupancy.availableBySize;

  const kpis = [
    {
      label: "Total Compartments",
      value: occupancy.total,
      sublabel: `Across ${stationCount} active ${
        stationCount === 1 ? "station" : "stations"
      }`,
      accentBg: "#EFF6FF",
      accentDot: "#0047AB",
    },
    {
      label: "Available Doors",
      value: occupancy.available,
      sublabel: `S: ${SMALL} • M: ${MEDIUM} • L: ${LARGE}`,
      accentBg: "#DCFCE7",
      accentDot: "#16A34A",
    },
    {
      label: "In Use (Reserved / Occupied)",
      value: inUse,
      sublabel: `${occupancy.reserved} reserved • ${occupancy.occupied} occupied`,
      accentBg: "#E0E7FF",
      accentDot: "#4F46E5",
    },
    {
      label: "Occupancy Rate",
      value: `${occupancy.occupancyRate}%`,
      sublabel: `${occupancy.maintenance} door(s) in maintenance`,
      accentBg: "#F1F5F9",
      accentDot: "#64748B",
    },
  ];

  return (
    <Grid container spacing={2.5} sx={styles.grid}>
      {kpis.map((item) => (
        <Grid key={item.label} size={{ xs: 12, sm: 6, lg: 3 }}>
          <Card elevation={0} sx={styles.kpiCard}>
            <CardContent sx={styles.cardContent}>
              <Box sx={styles.headerRow}>
                <Typography variant="subtitle2" sx={styles.label}>
                  {item.label}
                </Typography>
                <Box sx={{ ...styles.badgeBox, bgcolor: item.accentBg }}>
                  <Box sx={{ ...styles.dot, bgcolor: item.accentDot }} />
                </Box>
              </Box>

              <Typography variant="h4" sx={styles.value}>
                {item.value}
              </Typography>

              <Typography variant="caption" sx={styles.sublabel}>
                {item.sublabel}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  grid: {
    mb: 3.5,
  },
  kpiCard: {
    borderRadius: 3,
    border: "1px solid #E2E8F0",
    bgcolor: "#FFFFFF",
    height: "100%",
  },
  cardContent: {
    p: 2.5,
  },
  headerRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    mb: 1.25,
  },
  label: {
    fontWeight: 700,
    color: "text.secondary",
  },
  badgeBox: {
    width: 28,
    height: 28,
    borderRadius: 1.5,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
  },
  value: {
    fontWeight: 800,
    color: "text.primary",
    mb: 0.5,
  },
  sublabel: {
    color: "text.secondary",
    fontWeight: 500,
  },
};
