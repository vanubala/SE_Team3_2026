import { createTheme } from '@mui/material/styles';

export const splsTheme = createTheme({
  palette: {
    primary: {
      main: '#0047AB',      // Pickup.fr Cobalt Royal Blue
      light: '#E3F2FD',     // Soft Ice-Blue callout tint
      dark: '#003380',      // Deep Royal Blue hover
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#1D4ED8',      // Bright Royal Blue accent
      light: '#EFF6FF',
      dark: '#1E3A8A',
      contrastText: '#FFFFFF',
    },
    success: {
      main: '#0047AB',      // Keep primary CTAs unified in Cobalt Blue
      dark: '#003380',
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#DC2626',
    },
    background: {
      default: '#FFFFFF',   // Pure white canvas matching screenshot
      paper: '#F8FAFC',
    },
    text: {
      primary: '#111827',   // Crisp dark headings
      secondary: '#64748B', // Muted slate subtext
    },
    divider: '#E2E8F0',
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: { fontWeight: 800, letterSpacing: '-0.02em' },
    h5: { fontWeight: 700 },
    h6: { fontWeight: 700 },
    button: { fontWeight: 700, textTransform: 'none' },
  },
  shape: {
    borderRadius: 12,
  },
});