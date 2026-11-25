import { useState } from "react";
import {
  Box,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
  type SxProps,
  type Theme,
} from "@mui/material";

export type KioskLanguage = "FR" | "EN" | "DE" | "LU";

interface KioskHeaderProps {
  stationName: string;
}

const LANGUAGES: KioskLanguage[] = ["FR", "EN", "DE", "LU"];

export function KioskHeader({ stationName }: KioskHeaderProps) {
  const [lang, setLang] = useState<KioskLanguage>("EN");

  return (
    <Box sx={styles.headerBar}>
      <Box>
        <Typography variant="overline" sx={styles.brandLabel}>
          SMART LOCKER TERMINAL
        </Typography>
        <Typography variant="subtitle1" sx={styles.stationName}>
          {stationName}
        </Typography>
      </Box>

      <Stack direction="row" spacing={1.5} sx={styles.rightControls}>
        <ToggleButtonGroup
          size="small"
          exclusive
          value={lang}
          onChange={(_, nextLang: KioskLanguage | null) => {
            if (nextLang) setLang(nextLang);
          }}
          aria-label="Language selector"
          sx={styles.langGroup}
        >
          {LANGUAGES.map((code) => (
            <ToggleButton key={code} value={code} sx={styles.langButton}>
              {code}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Stack>
    </Box>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  headerBar: {
    bgcolor: "#FFFFFF",
    px: { xs: 2.5, sm: 4 },
    py: 2,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottom: "1px solid",
    borderColor: "divider",
  },
  brandLabel: {
    display: "block",
    lineHeight: 1.2,
    fontWeight: 800,
    color: "primary.main",
    letterSpacing: 1,
  },
  stationName: {
    fontWeight: 700,
    color: "text.primary",
  },
  rightControls: {
    alignItems: "center",
  },
  langGroup: {
    bgcolor: "#F8FAFC",
    borderRadius: 2,
  },
  langButton: {
    px: 1.25,
    py: 0.4,
    fontSize: "0.75rem",
    fontWeight: 700,
    color: "text.secondary",
    borderColor: "#E2E8F0",
    "&.Mui-selected": {
      bgcolor: "primary.main",
      color: "#FFFFFF",
      "&:hover": {
        bgcolor: "primary.dark",
      },
    },
  },
};
