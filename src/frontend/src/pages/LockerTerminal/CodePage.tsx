import { useState, type SubmitEvent } from "react";
import {
  Navigate,
  useNavigate,
  useOutletContext,
  useParams,
} from "react-router-dom";
import { terminalApi } from "../../api/terminalApi";
import { CodeEntryStep } from "../../components/LockerTerminal/CodeEntry";
import type { TerminalOutletContext } from "../../components/LockerTerminal/TerminalLayout";
import { TerminalApiError, type TerminalMode } from "../../types/terminal";

export function TerminalCodePage() {
  const { mode: routeMode } = useParams<{ mode: string }>();
  const navigate = useNavigate();
  const { lockerId, setFeedback } = useOutletContext<TerminalOutletContext>();

  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [lockedUntil, setLockedUntil] = useState<number | null>(null);

  if (routeMode !== "pickup" && routeMode !== "deposit") {
    return <Navigate to="/terminal" replace />;
  }

  const mode: TerminalMode = routeMode === "pickup" ? "PICKUP" : "DEPOSIT";
  const isLocked = lockedUntil !== null && Date.now() < lockedUntil;

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!code.trim() || loading || (mode === "PICKUP" && isLocked)) return;

    setLoading(true);
    setFeedback(null);

    try {
      if (mode === "PICKUP") {
        const res = await terminalApi.verifyPickupPin(lockerId, code.trim());
        navigate("/terminal/door-open", {
          state: {
            mode,
            parcelId: res.parcelId,
            compartmentId: res.compartmentId,
            compartmentNumber: res.compartmentNumber,
            pickupSessionToken: res.pickupSessionToken,
          },
        });
      } else {
        const res = await terminalApi.unlockForDeposit(lockerId, code.trim());
        navigate("/terminal/door-open", {
          state: {
            mode,
            parcelId: res.parcelId,
            compartmentId: res.compartmentId,
            compartmentNumber: res.compartmentNumber,
          },
        });
      }
    } catch (err) {
      if (err instanceof TerminalApiError) {
        if (err.code === "LOCKED") {
          setLockedUntil(Date.now() + (err.retryAfterSeconds ?? 900) * 1000);
          setFeedback({
            severity: "error",
            message:
              "Terminal locked for 15 minutes due to 5 failed PIN attempts.",
          });
          return;
        }
        const attempts =
          err.remainingAttempts !== undefined
            ? ` (${err.remainingAttempts} attempts remaining)`
            : "";
        setFeedback({
          severity: "error",
          message: `${err.message}${attempts}`,
        });
      } else {
        setFeedback({
          severity: "error",
          message: "Unexpected terminal error.",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <CodeEntryStep
      mode={mode}
      code={code}
      loading={loading}
      isLocked={isLocked}
      onCodeChange={setCode}
      onSubmit={handleSubmit}
      onBack={() => {
        setFeedback(null);
        navigate("/terminal");
      }}
    />
  );
}
