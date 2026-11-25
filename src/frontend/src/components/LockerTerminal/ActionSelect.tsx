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
        {/* PICK UP — Primary / Most Frequent Action (Filled Cobalt Blue Circle) */}
        <Card elevation={3} sx={styles.pickupFilledCircle}>
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
                stroke="#FFFFFF"
                strokeWidth="1.9"
              >
                <path d="M21 10V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l2-1.14" />
                <path d="m3.3 7 8.7 5 8.7-5" />
                <path d="M12 22V12" />
                <path d="m16 19 2 2 4-4" />
              </svg>
            </Box>
            <Typography variant="h6" sx={styles.filledCircleLabel}>
              PICK UP
            </Typography>
            <Typography variant="caption" sx={styles.filledCircleSubtext}>
              Collect a Parcel
            </Typography>
          </CardActionArea>
        </Card>

        {/* DROP OFF — Secondary Action (Outlined White Circle) */}
        <Card elevation={0} sx={styles.depositOutlinedCircle}>
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
                stroke="#0047AB"
                strokeWidth="1.9"
              >
                <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
                <path d="m3.3 7 8.7 5 8.7-5" />
                <path d="M12 22V12" />
              </svg>
            </Box>
            <Typography variant="h6" sx={styles.outlinedCircleLabel}>
              DROP OFF
            </Typography>
            <Typography variant="caption" sx={styles.outlinedCircleSubtext}>
              Courier Deposit
            </Typography>
          </CardActionArea>
        </Card>
      </Stack>
    </Box>
  );
}

const baseCircleCard: SxProps<Theme> = {
  width: 215,
  height: 215,
  borderRadius: "50%",
  transition:
    "transform 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease",
  "&:hover": {
    transform: "scale(1.04)",
  },
};

const styles: Record<string, SxProps<Theme>> = {
  container: {
    textAlign: "center",
  },
  welcomeTitle: {
    color: "text.primary",
    mb: 0.75,
  },
  subtitle: {
    color: "primary.main",
    fontWeight: 600,
    mb: 4.5,
  },
  buttonRow: {
    justifyContent: "center",
    alignItems: "center",
  },
  pickupFilledCircle: {
    ...baseCircleCard,
    bgcolor: "primary.main",
    color: "#FFFFFF",
    "&:hover": {
      transform: "scale(1.04)",
      bgcolor: "primary.dark",
      boxShadow: 6,
    },
  },
  depositOutlinedCircle: {
    ...baseCircleCard,
    bgcolor: "#FFFFFF",
    border: "2px solid",
    borderColor: "primary.main",
    "&:hover": {
      transform: "scale(1.04)",
      bgcolor: "#E3F2FD",
      boxShadow: 3,
    },
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
  filledCircleLabel: {
    color: "#FFFFFF",
    fontWeight: 800,
  },
  filledCircleSubtext: {
    color: "rgba(255, 255, 255, 0.85)",
  },
  outlinedCircleLabel: {
    color: "primary.main",
    fontWeight: 800,
  },
  outlinedCircleSubtext: {
    color: "text.secondary",
  },
};
