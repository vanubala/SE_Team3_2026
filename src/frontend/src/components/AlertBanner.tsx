interface AlertBannerProps {
  type: "success" | "error" | "warning";
  message: string;
}

const STYLES: Record<AlertBannerProps["type"], React.CSSProperties> = {
  success: {
    backgroundColor: "#dcfce7",
    color: "#166534",
    border: "1px solid #86efac",
  },
  error: {
    backgroundColor: "#fee2e2",
    color: "#991b1b",
    border: "1px solid #fca5a5",
  },
  warning: {
    backgroundColor: "#fef3c7",
    color: "#92400e",
    border: "1px solid #fcd34d",
  },
};

export function AlertBanner({ type, message }: AlertBannerProps) {
  return (
    <div
      role="alert"
      style={{
        ...STYLES[type],
        padding: "12px 16px",
        borderRadius: "8px",
        marginBottom: "16px",
        fontWeight: 500,
      }}
    >
      {message}
    </div>
  );
}
