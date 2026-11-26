import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import type { Parcel } from "../../types/domain";

interface CourierStatsRowProps {
  parcels: Parcel[];
}

export function CourierStatsRow({ parcels }: CourierStatsRowProps) {
  const awaitingAssignment = parcels.filter(
    (p) => p.status === "REGISTERED"
  ).length;
  const readyForDropOff = parcels.filter((p) => p.status === "ASSIGNED").length;
  const activeOrCollected = parcels.filter(
    (p) => p.status === "READY_FOR_PICKUP" || p.status === "COLLECTED"
  ).length;

  const cards = [
    {
      label: "Awaiting Assignment",
      sublabel: "Registered parcels needing a compartment",
      value: awaitingAssignment,
      highlight: true,
    },
    {
      label: "Ready for Drop-Off",
      sublabel: "Parcels ready for delivery",
      value: readyForDropOff,
      highlight: false,
    },
    {
      label: "Delivered",
      sublabel: "Parcels deposited in lockers",
      value: activeOrCollected,
      highlight: false,
    },
  ];

  return (
    <Grid container spacing={2.5} sx={styles.grid}>
      {cards.map((item) => (
        <Grid key={item.label} size={{ xs: 12, md: 4 }}>
          <Card
            elevation={0}
            sx={item.highlight ? styles.highlightCard : styles.standardCard}
          >
            <CardContent sx={styles.cardContent}>
              <Box sx={styles.topRow}>
                <Typography variant="subtitle2" sx={styles.cardLabel}>
                  {item.label}
                </Typography>
                <Box sx={item.highlight ? styles.activeDot : styles.mutedDot} />
              </Box>
              <Typography variant="h3" sx={styles.metricValue}>
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

const baseCard: SxProps<Theme> = {
  borderRadius: 3,
  border: "1px solid #E2E8F0",
  height: "100%",
};

const styles: Record<string, SxProps<Theme>> = {
  grid: {
    mb: 3.5,
  },
  highlightCard: {
    ...baseCard,
    bgcolor: "#E3F2FD",
    borderColor: "#BFDBFE",
  },
  standardCard: {
    ...baseCard,
    bgcolor: "#FFFFFF",
  },
  cardContent: {
    p: 2.5,
  },
  topRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    mb: 1,
  },
  cardLabel: {
    fontWeight: 700,
    color: "primary.main",
  },
  activeDot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    bgcolor: "primary.main",
  },
  mutedDot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    bgcolor: "#CBD5E1",
  },
  metricValue: {
    fontWeight: 800,
    color: "text.primary",
    mb: 0.5,
  },
  sublabel: {
    color: "text.secondary",
  },
};
