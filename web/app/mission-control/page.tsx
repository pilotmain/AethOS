import dynamic from "next/dynamic";

const MissionControlClient = dynamic(() => import("./MissionControlClient"), {
  loading: () => null,
});

export default function MissionControlPage() {
  return <MissionControlClient />;
}
