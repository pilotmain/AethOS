import { ArbiterPanel } from "@/components/ArbiterPanel";

export const metadata = {
  title: "Multi-Model Arbiter · AethOS",
};

export default function ArbiterPage() {
  return (
    <main style={{ minHeight: "100vh", background: "#0b1120", color: "#e2e8f0" }}>
      <ArbiterPanel />
    </main>
  );
}
