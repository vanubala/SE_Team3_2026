import { useState } from "react";
import { Outlet } from "react-router-dom";
import {
  Alert,
  Box,
  Container,
  Link,
  Paper,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import { KioskHeader } from "./KioskHeader";

export interface TerminalOutletContext {
  lockerId: string;
  setFeedback: (
    fb: { severity: "success" | "error" | "warning"; message: string } | null
  ) => void;
}

const STATION = {
  id: "loc-belval-01",
  name: "Maison du Savoir — Belval Campus",
};

export function TerminalLayout() {
  const [feedback, setFeedback] = useState<{
    severity: "success" | "error" | "warning";
    message: string;
  } | null>(null);

  return (
    <Box sx={styles.pageWrapper}>
      <Container maxWidth="md">
        <Paper elevation={2} sx={styles.kioskFrame}>
          <KioskHeader stationName={STATION.name} />

          <Box sx={styles.screenArea}>
            {feedback && (
              <Alert severity={feedback.severity} sx={styles.feedbackAlert}>
                {feedback.message}
              </Alert>
            )}

            <Outlet
              context={
                {
                  lockerId: STATION.id,
                  setFeedback,
                } satisfies TerminalOutletContext
              }
            />
          </Box>

          <Box sx={styles.footerBar}>
            <Typography variant="caption" sx={styles.footerText}>
              Need assistance with a compartment or pickup code?
            </Typography>
            <Link
              component="button"
              type="button"
              underline="hover"
              onClick={() => {}}
              sx={styles.supportLink}
            >
              Help &amp; Support
            </Link>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  pageWrapper: {
    minHeight: "100vh",
    bgcolor: "#F8FAFC",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    p: 2,
  },
  kioskFrame: {
    borderRadius: 4,
    overflow: "hidden",
    border: "1px solid #CBD5E1",
    boxShadow: "0 12px 32px rgba(15, 23, 42, 0.08)",
    bgcolor: "#FFFFFF",
  },
  screenArea: {
    p: { xs: 3, sm: 5 },
    minHeight: 430,
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
  },
  feedbackAlert: {
    mb: 3,
    borderRadius: 2,
  },
  footerBar: {
    px: { xs: 2.5, sm: 4 },
    py: 1.5,
    bgcolor: "#F8FAFC",
    borderTop: "1px solid",
    borderColor: "divider",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: 1,
  },
  footerText: {
    color: "text.secondary",
  },
  supportLink: {
    fontSize: "0.8rem",
    fontWeight: 700,
    color: "primary.main",
    cursor: "pointer",
  },
};
