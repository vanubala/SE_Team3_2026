import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { TerminalLayout } from './components/LockerTerminal/TerminalLayout';
import { TerminalCodePage } from './pages/LockerTerminal/CodePage';
import { TerminalDoorPage } from './pages/LockerTerminal/DoorPage';
import { TerminalHomePage } from './pages/LockerTerminal/HomePage';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/terminal" element={<TerminalLayout />}>
          <Route index element={<TerminalHomePage />} />
          <Route path=":mode" element={<TerminalCodePage />} />
          <Route path="door-open" element={<TerminalDoorPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/terminal" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;