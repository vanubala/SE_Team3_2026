import type {
  Compartment,
  CompartmentStatus,
  LockerOperationalStatus,
  LockerStation,
  SizeCategory,
} from "../types/domain";
import { apiRequest } from "./client";

export interface StationOccupancy {
  total: number;
  available: number;
  reserved: number;
  occupied: number;
  maintenance: number;
  occupancyRate: number;
  availableBySize: Record<SizeCategory, number>;
}

export interface AdminLockerOverview extends LockerStation {
  occupancy: StationOccupancy;
}

export interface StatusUpdateResult {
  targetId: string;
  status: string;
  warning: string | null;
}

interface RawAdminLocker {
  lockerId?: string;
  locker_id?: string;
  name: string;
  address?: string;
  openingHours?: string;
  opening_hours?: string;
  operationalStatus?: LockerOperationalStatus;
  operational_status?: LockerOperationalStatus;
  occupancy: {
    total: number;
    available: number;
    reserved: number;
    occupied: number;
    maintenance: number;
    occupancyRate?: number;
    occupancy_rate?: number;
    availableBySize?: Record<SizeCategory, number>;
    available_by_size?: Record<SizeCategory, number>;
  };
  compartments: Array<{
    compartmentId?: string;
    compartment_id?: string;
    number?: number;
    compartmentNumber?: number;
    compartment_number?: number;
    size?: SizeCategory;
    sizeCategory?: SizeCategory;
    size_category?: SizeCategory;
    status: CompartmentStatus;
  }>;
}

function mapAdminLocker(raw: RawAdminLocker): AdminLockerOverview {
  const compartments: Compartment[] = raw.compartments.map((c) => ({
    compartmentId: (c.compartmentId ?? c.compartment_id) as string,
    compartmentNumber: (c.number ??
      c.compartmentNumber ??
      c.compartment_number) as number,
    sizeCategory: (c.size ?? c.sizeCategory ?? c.size_category) as SizeCategory,
    status: c.status,
  }));

  return {
    lockerId: (raw.lockerId ?? raw.locker_id) as string,
    name: raw.name,
    address: raw.address ?? "Station Address Unavailable",
    openingHours: raw.openingHours ?? raw.opening_hours ?? "24/7",
    operationalStatus: (raw.operationalStatus ??
      raw.operational_status) as LockerOperationalStatus,
    occupancy: {
      total: raw.occupancy.total,
      available: raw.occupancy.available,
      reserved: raw.occupancy.reserved,
      occupied: raw.occupancy.occupied,
      maintenance: raw.occupancy.maintenance,
      occupancyRate:
        raw.occupancy.occupancyRate ?? raw.occupancy.occupancy_rate ?? 0,
      availableBySize: raw.occupancy.availableBySize ??
        raw.occupancy.available_by_size ?? { SMALL: 0, MEDIUM: 0, LARGE: 0 },
    },
    compartments,
  };
}

export const adminApi = {
  // FR_09: Fetch all stations with occupancy figures and compartment grids
  getLockersOverview: async (): Promise<AdminLockerOverview[]> => {
    const rawList = await apiRequest<RawAdminLocker[]>("/admin/lockers");
    return rawList.map(mapAdminLocker);
  },

  // FR_10: Toggle an individual compartment between AVAILABLE and MAINTENANCE
  updateCompartmentStatus: async (
    compartmentId: string,
    status: "AVAILABLE" | "MAINTENANCE"
  ): Promise<StatusUpdateResult> => {
    const raw = await apiRequest<{
      compartmentId?: string;
      compartment_id?: string;
      status: string;
      warning?: string | null;
    }>(`/admin/compartments/${encodeURIComponent(compartmentId)}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });

    return {
      targetId: (raw.compartmentId ??
        raw.compartment_id ??
        compartmentId) as string,
      status: raw.status,
      warning: raw.warning ?? null,
    };
  },

  // FR_10: Change whole-station operational status (ONLINE / MAINTENANCE / OFFLINE)
  updateLockerStatus: async (
    lockerId: string,
    operationalStatus: LockerOperationalStatus
  ): Promise<StatusUpdateResult> => {
    const raw = await apiRequest<{
      lockerId?: string;
      locker_id?: string;
      operationalStatus?: string;
      operational_status?: string;
      warning?: string | null;
    }>(`/admin/lockers/${encodeURIComponent(lockerId)}/status`, {
      method: "PATCH",
      body: JSON.stringify({ operationalStatus }),
    });

    return {
      targetId: (raw.lockerId ?? raw.locker_id ?? lockerId) as string,
      status: (raw.operationalStatus ??
        raw.operational_status ??
        operationalStatus) as string,
      warning: raw.warning ?? null,
    };
  },
};
