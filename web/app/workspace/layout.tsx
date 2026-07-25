// Workspace surfaces (Model Foundry, Email, Calendar, Notes, Documents) render
// into the global `html, body { overflow: hidden }` body, which has no inner
// scroll container of its own (unlike the chat shell). Without this wrapper, any
// panel content below the fold — the model-fit list, a long inbox — is clipped
// and unscrollable. A dedicated viewport-height scroll container lets the panel
// body scroll while the global body stays fixed; `min-height: 0` keeps the
// flexbox overflow trap from pinning children to their content height.
export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        height: "100vh",
        overflowY: "auto",
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {children}
    </div>
  );
}
