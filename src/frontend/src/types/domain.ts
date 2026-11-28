export type UserRole = "COURIER" | "ADMIN";
export type SizeCategory = "SMALL" | "MEDIUM" | "LARGE";
export type ParcelStatus =
  | "REGISTERED"
  | "ASSIGNED"
  | "READY_FOR_PICKUP"
  | "COLLECTED"
  | "EXPIRED";
export type CompartmentStatus =
  | "AVAILABLE"
  | "RESERVED"
  | "OCCUPIED"
  | "MAINTENANCE";
export type LockerOperationalStatus = "ONLINE" | "OFFLINE" | "MAINTENANCE";

export interface AuthUser {
  userId: string;
  name: string;
  email?: string;
  role: UserRole;
}

export interface LoginResponse {
  token: string;
  user: AuthUser;
}

export interface Parcel {
  parcelId: string;
  trackingNumber: string;
  sizeCategory: SizeCategory;
  status: ParcelStatus;
  preferredLockerId?: string;
  lockerName?: string;
  compartmentId?: string;
  compartmentNumber?: number;
  recipientContact: string;
  expectedDelivery?: string;
  notes?: string;
  registeredAt?: string;
  pickupDeadline?: string;
}

export interface Compartment {
  compartmentId: string;
  compartmentNumber: number;
  sizeCategory: SizeCategory;
  status: CompartmentStatus;
}

export interface LockerStation {
  lockerId: string;
  name: string;
  address: string;
  openingHours: string;
  operationalStatus: LockerOperationalStatus;
  compartments: Compartment[];
}

export class ApiError extends Error {
  readonly status: number;
  readonly code:
    | "UNAUTHORIZED"
    | "FORBIDDEN"
    | "NOT_FOUND"
    | "CONFLICT"
    | "VALIDATION"
    | "NETWORK";

  constructor(message: string, status: number, code: ApiError["code"]) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}
