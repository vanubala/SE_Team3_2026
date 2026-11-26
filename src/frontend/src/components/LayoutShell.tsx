import { Link as RouterLink, Outlet, useNavigate } from "react-router-dom";
import {
  AppBar,
  Box,
  Button,
  Chip,
  Container,
  Stack,
  Toolbar,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";
import { useAuth } from "../context/AuthContext";

export function LayoutShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <Box sx={styles.root}>
      <AppBar position="sticky" elevation={0} sx={styles.appBar}>
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={styles.toolbar}>
            <Stack direction="row" spacing={1.5} sx={styles.brandGroup}>
              <Box sx={styles.logoMark}>Smart Parcel Locker</Box>
            </Stack>

            <Stack direction="row" spacing={2} sx={styles.navActions}>
              <Button
                component={RouterLink}
                to="/terminal"
                variant="outlined"
                size="small"
                sx={styles.terminalLinkBtn}
              >
                Open Terminal View ↗
              </Button>

              {user && (
                <>
                  <Stack direction="row" spacing={1} sx={styles.userBadgeGroup}>
                    <Typography variant="body2" sx={styles.userName}>
                      {user.name}
                    </Typography>
                    <Chip label={user.role} size="small" sx={styles.roleChip} />
                  </Stack>

                  <Button
                    variant="contained"
                    size="small"
                    onClick={handleLogout}
                    sx={styles.logoutBtn}
                  >
                    Logout
                  </Button>
                </>
              )}
            </Stack>
          </Toolbar>
        </Container>
      </AppBar>

      <Container maxWidth="lg" sx={styles.mainContent}>
        <Outlet />
      </Container>
    </Box>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  root: {
    minHeight: "100vh",
    bgcolor: "#F8FAFC",
    display: "flex",
    flexDirection: "column",
  },
  appBar: {
    bgcolor: "#FFFFFF",
    color: "text.primary",
    borderBottom: "2px solid",
    borderColor: "primary.main",
  },
  toolbar: {
    justifyContent: "space-between",
    minHeight: 68,
    gap: 2,
  },
  brandGroup: {
    alignItems: "center",
  },
  logoMark: {
    bgcolor: "primary.main",
    color: "#FFFFFF",
    fontWeight: 800,
    fontSize: "0.85rem",
    letterSpacing: 1,
    px: 1.25,
    py: 0.5,
    borderRadius: 1.5,
  },
  brandTitle: {
    fontWeight: 800,
    color: "text.primary",
    display: { xs: "none", sm: "block" },
  },
  navActions: {
    alignItems: "center",
  },
  terminalLinkBtn: {
    borderColor: "primary.main",
    color: "primary.main",
    fontWeight: 700,
    borderRadius: 2,
    "&:hover": {
      bgcolor: "#E3F2FD",
      borderColor: "primary.dark",
    },
  },
  userBadgeGroup: {
    alignItems: "center",
    display: { xs: "none", md: "flex" },
  },
  userName: {
    fontWeight: 600,
    color: "text.primary",
  },
  roleChip: {
    bgcolor: "#E3F2FD",
    color: "primary.main",
    fontWeight: 800,
    fontSize: "0.7rem",
  },
  logoutBtn: {
    bgcolor: "primary.main",
    borderRadius: 2,
    "&:hover": {
      bgcolor: "primary.dark",
    },
  },
  mainContent: {
    pt: 5,
    pb: 6,
    flex: 1,
  },
};
