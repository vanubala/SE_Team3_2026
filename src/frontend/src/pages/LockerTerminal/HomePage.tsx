import { useNavigate, useOutletContext } from "react-router-dom";
import { ActionSelectStep } from "../../components/LockerTerminal/ActionSelect";
import type { TerminalOutletContext } from "../../components/LockerTerminal/TerminalLayout";
import type { TerminalMode } from "../../types/terminal";

export function TerminalHomePage() {
  const navigate = useNavigate();
  const { setFeedback } = useOutletContext<TerminalOutletContext>();

  const handleSelectMode = (mode: TerminalMode) => {
    setFeedback(null);
    navigate(mode === "PICKUP" ? "/terminal/pickup" : "/terminal/deposit");
  };

  return <ActionSelectStep onSelectMode={handleSelectMode} />;
}
