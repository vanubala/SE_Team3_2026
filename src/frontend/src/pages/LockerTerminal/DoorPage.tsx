import { useState } from "react";
import {
  Navigate,
  useLocation,
  useNavigate,
  useOutletContext,
} from "react-router-dom";
import { terminalApi } from "../../api/terminalApi";
import { DoorOpenStep } from "../../components/LockerTerminal/DoorOpen";
import type { TerminalOutletContext } from "../../components/LockerTerminal/TerminalLayout";
import { TerminalApiError, type TerminalMode } from "../../types/terminal";

interface DoorLocationState {
  mode: TerminalMode;
  parcelId: string;
  compartmentNumber: number;
  compartmentId?: string;
}

export function TerminalDoorPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { setFeedback } = useOutletContext<TerminalOutletContext>();
  const [loading, setLoading] = useState(false);

  const state = location.state as DoorLocationState | null;

  // Guard: if someone opens /terminal/door-open directly without unlocking a box first
  if (!state) {
    return <Navigate to="/terminal" replace />;
  }

  const handleConfirmClose = async () => {
    if (loading) return;
    setLoading(true);
    setFeedback(null);

    try {
      if (state.mode === "PICKUP" && state.compartmentId) {
        await terminalApi.confirmPickup(state.parcelId, state.compartmentId);
        setFeedback({
          severity: "success",
          message: `Compartment #${state.compartmentNumber} closed. Parcel collected—thank you!`,
        });
      } else {
        await terminalApi.confirmDeposit(
          state.parcelId,
          state.compartmentNumber
        );
        setFeedback({
          severity: "success",
          message: `Compartment #${state.compartmentNumber} closed. Parcel deposited & recipient notified!`,
        });
      }
      navigate("/terminal", { replace: true });
    } catch (err) {
      const msg =
        err instanceof TerminalApiError
          ? err.message
          : "Failed to confirm door closure.";
      setFeedback({ severity: "error", message: msg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <DoorOpenStep
      mode={state.mode}
      compartmentNumber={state.compartmentNumber}
      parcelId={state.parcelId}
      loading={loading}
      onConfirmClose={handleConfirmClose}
    />
  );
}
