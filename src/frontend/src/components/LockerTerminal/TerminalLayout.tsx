import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Alert, Box, Container, Paper, type SxProps, type Theme } from '@mui/material';
import { KioskHeader, type LockerStationOption } from './KioskHeader';

export interface TerminalOutletContext {
  lockerId: string;
  setFeedback: (fb: { severity: 'success' | 'error' | 'warning'; message: string } | null) => void;
}

const DEMO_STATIONS: LockerStationOption[] = [
  { id: 'loc-belval-01', name: 'Belval Plaza Station' },
  { id: 'loc-kirchberg-02', name: 'Kirchberg Gare Station' },
];

export function TerminalLayout() {
  const [lockerId, setLockerId] = useState(DEMO_STATIONS[0].id);
  const [feedback, setFeedback] = useState<{
    severity: 'success' | 'error' | 'warning';
    message: string;
  } | null>(null);

  const location = useLocation();
  const isDoorOpen = location.pathname.endsWith('/door-open');

  return (
    <Box sx={styles.pageWrapper}>
      <Container maxWidth="md">
        <Paper elevation={6} sx={styles.kioskFrame}>
          <KioskHeader
            stations={DEMO_STATIONS}
            selectedLockerId={lockerId}
            disabled={isDoorOpen}
            onSelectLocker={setLockerId}
          />

          <Box sx={styles.screenArea}>
            {feedback && (
              <Alert severity={feedback.severity} sx={styles.feedbackAlert}>
                {feedback.message}
              </Alert>
            )}

            <Outlet context={{ lockerId, setFeedback } satisfies TerminalOutletContext} />
          </Box>
        </Paper>
      </Container>
    </Box>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  pageWrapper: {
    minHeight: '100vh',
    bgcolor: '#f1f5f9',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    p: 2,
  },
  kioskFrame: {
    borderRadius: 4,
    overflow: 'hidden',
    border: '10px solid #1e293b',
    bgcolor: '#ffffff',
  },
  screenArea: {
    p: { xs: 3, sm: 5 },
    minHeight: 440,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
  },
  feedbackAlert: {
    mb: 3,
    borderRadius: 2,
  },
};