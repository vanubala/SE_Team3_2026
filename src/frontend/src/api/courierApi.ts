import type { Compartment, Parcel, SizeCategory } from "../types/domain";
import { apiRequest } from "./client";

export interface RegisterParcelInput {
  trackingNumber: string;
  sizeCategory: SizeCategory;
  recipientContact: string;
  expectedDelivery: string;
  preferredLockerId?: string;
  notes?: string;
}

export interface AvailableCompartmentsResult {
  lockerId: string;
  recommendedCompartmentId: string;
  availableCompartments: Compartment[];
}

export interface AssignCompartmentResult {
  parcelId: string;
  status: Parcel["status"];
  lockerId: string;
  compartmentId: string;
  compartmentNumber: number;
}

export interface LockerDetails {
  lockerId: string;
  name: string;
  address: string;
  openingHours: string;
  operationalStatus: "ONLINE" | "OFFLINE" | "MAINTENANCE";
}

interface ApiParcelDto {
  parcelId: string;
  trackingNumber: string;
  sizeCategory?: SizeCategory;
  status: Parcel["status"];
  preferredLockerId?: string | null;
  lockerName?: string | null;
  compartmentId?: string | null;
  compartmentNumber?: number | null;
  recipientContact?: string;
  expectedDelivery?: string | null;
  notes?: string | null;
  registeredAt?: string | null;
}

interface ApiCompartmentDto {
  compartmentId: string;
  compartmentNumber: number;
  sizeCategory: SizeCategory;
  status?: Compartment["status"];
}

function mapParcel(dto: ApiParcelDto, fallback?: Partial<Parcel>): Parcel {
  return {
    parcelId: dto.parcelId,
    trackingNumber: dto.trackingNumber,
    sizeCategory: dto.sizeCategory ?? fallback?.sizeCategory ?? "MEDIUM",
    status: dto.status,
    preferredLockerId: dto.preferredLockerId ?? fallback?.preferredLockerId,
    lockerName: dto.lockerName ?? fallback?.lockerName,
    compartmentId: dto.compartmentId ?? fallback?.compartmentId,
    compartmentNumber: dto.compartmentNumber ?? fallback?.compartmentNumber,
    recipientContact: dto.recipientContact ?? fallback?.recipientContact ?? "",
    expectedDelivery: dto.expectedDelivery ?? fallback?.expectedDelivery,
    notes: dto.notes ?? fallback?.notes,
    registeredAt: dto.registeredAt ?? fallback?.registeredAt,
  };
}

export const courierApi = {
  // UC1: List courier's parcels
  listParcels: async (status?: string): Promise<Parcel[]> => {
    const query =
      status && status !== "ALL" ? `?status=${encodeURIComponent(status)}` : "";
    const list = await apiRequest<ApiParcelDto[]>(`/parcels${query}`);
    return list.map((item) => mapParcel(item));
  },

  // UC1: Register a new parcel (RegisterParcelIn expects camelCase)
  registerParcel: async (input: RegisterParcelInput): Promise<Parcel> => {
    const trimmedTracking = input.trackingNumber.trim();
    const trimmedContact = input.recipientContact.trim();
    const isoDelivery = new Date(input.expectedDelivery).toISOString();
    const trimmedLocker = input.preferredLockerId?.trim() || null;
    const trimmedNotes = input.notes?.trim() || null;

    const dto = await apiRequest<ApiParcelDto>("/parcels", {
      method: "POST",
      body: JSON.stringify({
        trackingNumber: trimmedTracking,
        sizeCategory: input.sizeCategory,
        recipientContact: trimmedContact,
        expectedDelivery: isoDelivery,
        preferredLockerId: trimmedLocker,
        notes: trimmedNotes,
      }),
    });

    return mapParcel(dto, {
      sizeCategory: input.sizeCategory,
      recipientContact: trimmedContact,
      expectedDelivery: isoDelivery,
      preferredLockerId: trimmedLocker ?? undefined,
      notes: trimmedNotes ?? undefined,
    });
  },

  // UC2: Fetch available compartments + smallest-fit recommendation
  getAvailableCompartments: async (
    lockerId: string,
    size: SizeCategory
  ): Promise<AvailableCompartmentsResult> => {
    const res = await apiRequest<{
      lockerId: string;
      recommendedCompartmentId: string;
      availableCompartments: ApiCompartmentDto[];
    }>(`/lockers/${encodeURIComponent(lockerId)}/compartments?size=${size}`);

    return {
      lockerId: res.lockerId,
      recommendedCompartmentId: res.recommendedCompartmentId,
      availableCompartments: res.availableCompartments.map((c) => ({
        compartmentId: c.compartmentId,
        compartmentNumber: c.compartmentNumber,
        sizeCategory: c.sizeCategory,
        status: c.status ?? "AVAILABLE",
      })),
    };
  },

  // UC2: Assign compartment to a REGISTERED parcel (AssignIn expects camelCase)
  assignCompartment: async (
    parcelId: string,
    lockerId: string,
    compartmentId: string
  ): Promise<AssignCompartmentResult> => {
    return apiRequest<AssignCompartmentResult>(
      `/parcels/${encodeURIComponent(parcelId)}/assign`,
      {
        method: "POST",
        body: JSON.stringify({
          lockerId,
          compartmentId,
        }),
      }
    );
  },

  getLockerDetails: async (lockerId: string): Promise<LockerDetails> => {
    const raw = await apiRequest<{
      lockerId?: string;
      locker_id?: string;
      name: string;
      address?: string;
      openingHours?: string;
      opening_hours?: string;
      operationalStatus?: LockerDetails["operationalStatus"];
      operational_status?: LockerDetails["operationalStatus"];
    }>(`/lockers/${encodeURIComponent(lockerId)}`);

    return {
      lockerId: (raw.lockerId ?? raw.locker_id ?? lockerId) as string,
      name: raw.name,
      address: raw.address ?? "Address unavailable",
      openingHours: raw.openingHours ?? raw.opening_hours ?? "24/7",
      operationalStatus: (raw.operationalStatus ??
        raw.operational_status ??
        "ONLINE") as LockerDetails["operationalStatus"],
    };
  },
};
