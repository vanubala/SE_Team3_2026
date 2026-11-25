import {
  Box,
  MenuItem,
  Select,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";

export interface LockerStationOption {
  id: string;
  name: string;
}

interface KioskHeaderProps {
  stations: LockerStationOption[];
  selectedLockerId: string;
  disabled: boolean;
  onSelectLocker: (lockerId: string) => void;
}

export function KioskHeader({
  stations,
  selectedLockerId,
  disabled,
  onSelectLocker,
}: KioskHeaderProps) {
  return (
    <Box sx={styles.headerBar}>
      <Typography variant="subtitle1" sx={styles.title}>
        KIOSK TERMINAL
      </Typography>

      <Select
        size="small"
        value={selectedLockerId}
        disabled={disabled}
        onChange={(e) => onSelectLocker(e.target.value)}
        sx={styles.stationSelect}
      >
        {stations.map((station) => (
          <MenuItem key={station.id} value={station.id}>
            {station.name}
          </MenuItem>
        ))}
      </Select>
    </Box>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  headerBar: {
    bgcolor: "#334155",
    color: "#ffffff",
    px: 3,
    py: 1.5,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: {
    fontWeight: 700,
    letterSpacing: 0.5,
  },
  stationSelect: {
    bgcolor: "rgba(255,255,255,0.12)",
    color: "#fff",
    ".MuiOutlinedInput-notchedOutline": {
      borderColor: "rgba(255,255,255,0.3)",
    },
    ".MuiSvgIcon-root": { color: "#fff" },
  },
};
