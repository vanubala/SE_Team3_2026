import type { Compartment, Parcel, SizeCategory } from "../types/domain";
import { apiRequest } from "./client";

export interface RegisterParcelInput {
  trackingNumber: string;
  sizeCategory: SizeCategory;
  recipientContact: string;
  expectedDelivery: string; // ISO string
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

// Raw FastAPI snake_case DTOs from Member 3's schemas
interface RawParcel {
  parcel_id: string;
  tracking_number: string;
  size_category: SizeCategory;
  status: Parcel["status"];
  preferred_locker_id?: string | null;
  compartment_id?: string | null;
  compartment_number?: number | null;
  recipient_contact?: string;
  expected_delivery?: string | null;
  notes?: string | null;
  registered_at?: string | null;
}

interface RawCompartment {
  compartment_id: string;
  compartment_number: number;
  size_category: SizeCategory;
  status: Compartment["status"];
}

function mapParcel(raw: RawParcel): Parcel {
  return {
    parcelId: raw.parcel_id,
    trackingNumber: raw.tracking_number,
    sizeCategory: raw.size_category,
    status: raw.status,
    preferredLockerId: raw.preferred_locker_id ?? undefined,
    compartmentId: raw.compartment_id ?? undefined,
    compartmentNumber: raw.compartment_number ?? undefined,
    recipientContact: raw.recipient_contact ?? "",
    expectedDelivery: raw.expected_delivery ?? undefined,
    notes: raw.notes ?? undefined,
    registeredAt: raw.registered_at ?? undefined,
  };
}

export const courierApi = {
  // UC1: List courier's parcels
  listParcels: async (status?: string): Promise<Parcel[]> => {
    const query =
      status && status !== "ALL" ? `?status=${encodeURIComponent(status)}` : "";
    const rawList = await apiRequest<RawParcel[]>(`/parcels${query}`);
    return rawList.map(mapParcel);
  },

  // UC1: Register a new parcel
  registerParcel: async (input: RegisterParcelInput): Promise<Parcel> => {
    const raw = await apiRequest<RawParcel>("/parcels", {
      method: "POST",
      body: JSON.stringify({
        tracking_number: input.trackingNumber.trim(),
        size_category: input.sizeCategory,
        recipient_contact: input.recipientContact.trim(),
        expected_delivery: new Date(input.expectedDelivery).toISOString(),
        preferred_locker_id: input.preferredLockerId?.trim() || null,
        notes: input.notes?.trim() || null,
      }),
    });
    return mapParcel(raw);
  },

  // UC2: Fetch available compartments + smallest-fit recommendation
  getAvailableCompartments: async (
    lockerId: string,
    size: SizeCategory
  ): Promise<AvailableCompartmentsResult> => {
    const raw = await apiRequest<{
      locker_id: string;
      recommended_compartment_id: string;
      available_compartments: RawCompartment[];
    }>(`/lockers/${encodeURIComponent(lockerId)}/compartments?size=${size}`);

    return {
      lockerId: raw.locker_id,
      recommendedCompartmentId: raw.recommended_compartment_id,
      availableCompartments: raw.available_compartments.map((c) => ({
        compartmentId: c.compartment_id,
        compartmentNumber: c.compartment_number,
        sizeCategory: c.size_category,
        status: c.status,
      })),
    };
  },

  // UC2: Assign compartment to a REGISTERED parcel
  assignCompartment: async (
    parcelId: string,
    lockerId: string,
    compartmentId: string
  ): Promise<AssignCompartmentResult> => {
    const raw = await apiRequest<{
      parcel_id: string;
      status: Parcel["status"];
      locker_id: string;
      compartment_id: string;
      compartment_number: number;
    }>(`/parcels/${encodeURIComponent(parcelId)}/assign`, {
      method: "POST",
      body: JSON.stringify({
        locker_id: lockerId,
        compartment_id: compartmentId,
      }),
    });

    return {
      parcelId: raw.parcel_id,
      status: raw.status,
      lockerId: raw.locker_id,
      compartmentId: raw.compartment_id,
      compartmentNumber: raw.compartment_number,
    };
  },
};
