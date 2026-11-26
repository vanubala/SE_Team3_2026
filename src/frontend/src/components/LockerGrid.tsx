import { Box, Chip, Stack, Tooltip, Typography, type SxProps, type Theme } from '@mui/material';
import type { Compartment } from '../types/domain';

interface LockerBankGridProps {
  compartments: Compartment[];
  selectedCompartmentId?: string | null;
  recommendedCompartmentId?: string | null;
  isSelectable?: (compartment: Compartment) => boolean;
  onSelectCompartment?: (compartment: Compartment) => void;
}

const DOOR_STYLES: Record<
  Compartment['status'],
  { bg: string; border: string; text: string; dot: string }
> = {
  AVAILABLE: {
    bg: '#DCFCE7',
    border: '#86EFAC',
    text: '#166534',
    dot: '#16A34A',
  },
  RESERVED: {
    bg: '#DBEAFE',
    border: '#93C5FD',
    text: '#1E40AF',
    dot: '#2563EB',
  },
  OCCUPIED: {
    bg: '#E0E7FF',
    border: '#A5B4FC',
    text: '#3730A3',
    dot: '#4F46E5',
  },
  MAINTENANCE: {
    bg: '#F1F5F9',
    border: '#CBD5E1',
    text: '#475569',
    dot: '#94A3B8',
  },
};

export function LockerBankGrid({
  compartments,
  selectedCompartmentId,
  recommendedCompartmentId,
  isSelectable,
  onSelectCompartment,
}: LockerBankGridProps) {
  const sorted = [...compartments].sort((a, b) => a.compartmentNumber - b.compartmentNumber);

  return (
    <Box>
      <Stack direction="row" spacing={2.5} sx={styles.legendRow}>
        {[
          { label: 'Available', color: '#22C55E' },
          { label: 'Reserved', color: '#2563EB' },
          { label: 'Occupied', color: '#6366F1' },
          { label: 'Maintenance', color: '#94A3B8' },
        ].map((item) => (
          <Stack key={item.label} direction="row" spacing={0.75} sx={styles.legendItem}>
            <Box sx={{ ...styles.legendDot, bgcolor: item.color }} />
            <Typography variant="caption" sx={styles.legendText}>
              {item.label}
            </Typography>
          </Stack>
        ))}
      </Stack>

      {/* Physical Locker Bank Frame + Terminal Column */}
      <Box sx={styles.bankHousing}>
        <Box sx={styles.doorsGrid}>
          {sorted.map((comp) => {
            const palette = DOOR_STYLES[comp.status];
            const clickable = isSelectable ? isSelectable(comp) : false;
            const isSelected = comp.compartmentId === selectedCompartmentId;
            const isRecommended = comp.compartmentId === recommendedCompartmentId;

            return (
              <Tooltip
                key={comp.compartmentId}
                title={`Box #${comp.compartmentNumber} • ${comp.sizeCategory} • ${comp.status}${
                  isRecommended ? ' (Recommended)' : ''
                }`}
              >
                <Box
                  role={clickable ? 'button' : undefined}
                  tabIndex={clickable ? 0 : undefined}
                  onClick={() => {
                    if (clickable && onSelectCompartment) {
                      onSelectCompartment(comp);
                    }
                  }}
                  onKeyDown={(e) => {
                    if (clickable && onSelectCompartment && (e.key === 'Enter' || e.key === ' ')) {
                      e.preventDefault();
                      onSelectCompartment(comp);
                    }
                  }}
                  sx={{
                    ...styles.doorCell,
                    bgcolor: isSelected ? '#0047AB' : palette.bg,
                    borderColor: isSelected ? '#003380' : palette.border,
                    color: isSelected ? '#FFFFFF' : palette.text,
                    cursor: clickable ? 'pointer' : 'not-allowed',
                    opacity: clickable || !isSelectable ? 1 : 0.65,
                    boxShadow: isSelected ? '0 0 0 3px rgba(0, 71, 171, 0.25)' : 'none',
                    '&:hover': clickable
                      ? {
                          transform: 'translateY(-1px)',
                          boxShadow: '0 4px 10px rgba(15, 23, 42, 0.12)',
                        }
                      : undefined,
                  }}
                >
                  <Box sx={styles.doorHeader}>
                    <Typography variant="subtitle2" sx={styles.doorNumber}>
                      #{comp.compartmentNumber}
                    </Typography>
                    <Box
                      sx={{
                        ...styles.handleDot,
                        bgcolor: isSelected ? '#FFFFFF' : palette.dot,
                      }}
                    />
                  </Box>

                  <Typography variant="caption" sx={styles.doorSize}>
                    {comp.sizeCategory}
                  </Typography>

                  {isRecommended && (
                    <Chip
                      size="small"
                      label="Best Fit"
                      sx={isSelected ? styles.bestFitSelectedChip : styles.bestFitChip}
                    />
                  )}
                </Box>
              </Tooltip>
            );
          })}
        </Box>

        {/* Right-Hand Kiosk Terminal Column (from StrongPoint reference) */}
        <Box sx={styles.kioskColumn}>
          <Box sx={styles.kioskScreen}>
            <Typography variant="caption" sx={styles.kioskScreenText}>
              SPLS
            </Typography>
          </Box>
          <Box sx={styles.scannerSlot} />
        </Box>
      </Box>
    </Box>
  );
}

const styles: Record<string, SxProps<Theme>> = {
  legendRow: {
    flexWrap: 'wrap',
    mb: 1.5,
  },
  legendItem: {
    alignItems: 'center',
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: '50%',
  },
  legendText: {
    fontWeight: 600,
    color: 'text.secondary',
  },
  bankHousing: {
    display: 'flex',
    gap: 1.5,
    p: 1.5,
    bgcolor: '#E2E8F0',
    borderRadius: 2.5,
    border: '1px solid #CBD5E1',
  },
  doorsGrid: {
    flex: 1,
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(84px, 1fr))',
    gap: 1,
  },
  doorCell: {
    minHeight: 78,
    p: 1,
    borderRadius: 1.5,
    border: '2px solid',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    transition: 'transform 0.12s ease, box-shadow 0.12s ease, background-color 0.12s ease',
  },
  doorHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  doorNumber: {
    fontWeight: 800,
    lineHeight: 1.1,
  },
  handleDot: {
    width: 6,
    height: 6,
    borderRadius: '50%',
  },
  doorSize: {
    fontSize: '0.68rem',
    fontWeight: 700,
    opacity: 0.9,
  },
  bestFitChip: {
    height: 18,
    fontSize: '0.62rem',
    fontWeight: 800,
    bgcolor: 'primary.main',
    color: '#FFFFFF',
  },
  bestFitSelectedChip: {
    height: 18,
    fontSize: '0.62rem',
    fontWeight: 800,
    bgcolor: '#FFFFFF',
    color: 'primary.main',
  },
  kioskColumn: {
    width: 56,
    bgcolor: '#F8FAFC',
    borderRadius: 1.5,
    border: '1px solid #CBD5E1',
    display: { xs: 'none', sm: 'flex' },
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 1.5,
    p: 1,
  },
  kioskScreen: {
    width: 36,
    height: 48,
    borderRadius: 1,
    bgcolor: 'primary.main',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  kioskScreenText: {
    color: '#FFFFFF',
    fontWeight: 800,
    fontSize: '0.6rem',
    letterSpacing: 0.5,
  },
  scannerSlot: {
    width: 24,
    height: 6,
    borderRadius: 1,
    bgcolor: '#94A3B8',
  },
};