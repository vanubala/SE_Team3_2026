import {
  Box,
  Card,
  CardActionArea,
  Stack,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import type { TerminalMode } from "../../types/terminal";

interface ActionSelectStepProps {
  onSelectMode: (mode: TerminalMode) => void;
}

export function ActionSelectStep({ onSelectMode }: ActionSelectStepProps) {
  return (
    <Box sx={styles.container}>
      <Typography variant="h4" sx={styles.welcomeTitle}>
        Welcome!
      </Typography>
      <Typography variant="h5" sx={styles.subtitle}>
        What do you want to do?
      </Typography>

      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={4}
        sx={styles.buttonRow}
      >
        <Card elevation={2} sx={styles.depositCircleCard}>
          <CardActionArea
            onClick={() => onSelectMode("DEPOSIT")}
            sx={styles.circleActionArea}
          >
            <Box sx={styles.iconBox}>
              <svg
                width="52"
                height="52"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#0f172a"
                strokeWidth="1.8"
              >
                <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
                <path d="m3.3 7 8.7 5 8.7-5" />
                <path d="M12 22V12" />
              </svg>
            </Box>
            <Typography variant="h6" sx={styles.circleLabel}>
              DROP OFF
            </Typography>
            <Typography variant="caption" sx={styles.circleSubtext}>
              Courier Parcel Deposit
            </Typography>
          </CardActionArea>
        </Card>

        <Card elevation={2} sx={styles.pickupCircleCard}>
          <CardActionArea
            onClick={() => onSelectMode("PICKUP")}
            sx={styles.circleActionArea}
          >
            <Box sx={styles.iconBox}>
              <svg
                width="52"
                height="52"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#2e7d32"
                strokeWidth="1.8"
              >
                <path d="M21 10V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l2-1.14" />
                <path d="m3.3 7 8.7 5 8.7-5" />
                <path d="M12 22V12" />
                <path d="m16 19 2 2 4-4" />
              </svg>
            </Box>
            <Typography variant="h6" sx={styles.circleLabel}>
              PICK UP
            </Typography>
            <Typography variant="caption" sx={styles.circleSubtext}>
              Recipient Collection
            </Typography>
          </CardActionArea>
        </Card>
      </Stack>
    </Box>
  );
}

const baseCircleCard: SxProps<Theme> = {
  width: 210,
  height: 210,
  borderRadius: "50%",
  bgcolor: "#f8fafc",
  border: "2px solid #e2e8f0",
  transition: "transform 0.15s, border-color 0.15s",
};

const styles: Record<string, SxProps<Theme>> = {
  container: {
    textAlign: "center",
  },
  welcomeTitle: {
    fontWeight: 800,
    color: "#1e3a8a",
    mb: 1,
  },
  subtitle: {
    fontWeight: 600,
    color: "#1e40af",
    mb: 4,
  },
  buttonRow: {
    justifyContent: "center",
    alignItems: "center",
  },
  depositCircleCard: {
    ...baseCircleCard,
    "&:hover": { transform: "scale(1.04)", borderColor: "#2563eb" },
  },
  pickupCircleCard: {
    ...baseCircleCard,
    "&:hover": { transform: "scale(1.04)", borderColor: "#2e7d32" },
  },
  circleActionArea: {
    height: "100%",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    p: 2,
  },
  iconBox: {
    mb: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  circleLabel: {
    fontWeight: 800,
    color: "#0f172a",
  },
  circleSubtext: {
    color: "text.secondary",
  },
};
