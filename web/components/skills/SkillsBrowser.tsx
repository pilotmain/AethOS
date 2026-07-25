"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  fetchOperatorSkillDetail,
  fetchOperatorSkillsCatalog,
  type OperatorSkillDetail,
  type OperatorSkillSummary,
} from "@/lib/skills/skillsApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import { missionControlHref } from "@/lib/missionControl/deepLinks";

export function SkillsBrowser() {
  const [skills, setSkills] = useState<OperatorSkillSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<OperatorSkillDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCatalog = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const catalog = await fetchOperatorSkillsCatalog();
      setSkills(catalog.skills ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load skills");
      setSkills([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadCatalog();
  }, [loadCatalog]);

  useEffect(() => {
    if (skills.length > 0 && !selectedId) {
      setSelectedId(skills[0]!.id);
    }
  }, [skills, selectedId]);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    void fetchOperatorSkillDetail(selectedId)
      .then(setDetail)
      .catch(() => setDetail(null));
  }, [selectedId]);

  return (
    <div style={{ minHeight: "100vh", background: "var(--aethos-bg)", color: mcColors.text, padding: "24px 20px" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: mcColors.textDim }}>AETHOS</div>
            <h1 style={{ margin: "6px 0 4px", fontSize: 22, fontWeight: 700 }}>Skills</h1>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted, maxWidth: 520 }}>
              Operator playbooks from the repo <code style={{ fontSize: 12 }}>skills/</code> directory. Use{" "}
              <code style={{ fontSize: 12 }}>skill_recall</code> in Agent mode to load them in chat.
            </p>
          </div>
          <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
            <Link href="/" style={{ ...mcButtonSecondaryStyle, textDecoration: "none", fontSize: 12 }}>
              ← Chat
            </Link>
            <Link href={missionControlHref("home")} style={{ ...mcButtonSecondaryStyle, textDecoration: "none", fontSize: 12 }}>
              Mission Control
            </Link>
          </div>
        </div>

        {loading ? <p style={{ color: mcColors.textMuted, fontSize: 13 }}>Loading skills…</p> : null}
        {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

        {!loading && skills.length === 0 ? (
          <section style={mcPanelSectionStyle}>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>
              No skills found. Add a folder under <code>skills/your-skill/SKILL.md</code>.
            </p>
          </section>
        ) : null}

        {skills.length > 0 ? (
          <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: 16, alignItems: "start" }}>
            <nav
              style={{
                ...mcPanelSectionStyle,
                padding: 8,
                maxHeight: "70vh",
                overflowY: "auto",
              }}
            >
              {skills.map((skill) => {
                const active = skill.id === selectedId;
                return (
                  <button
                    key={skill.id}
                    type="button"
                    onClick={() => setSelectedId(skill.id)}
                    style={{
                      display: "block",
                      width: "100%",
                      textAlign: "left",
                      padding: "10px 12px",
                      marginBottom: 4,
                      borderRadius: 10,
                      border: "none",
                      cursor: "pointer",
                      background: active ? "rgba(34,211,238,0.12)" : "transparent",
                      color: active ? mcColors.cyan : mcColors.text,
                    }}
                  >
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{skill.name || skill.id}</div>
                    {skill.description ? (
                      <div style={{ fontSize: 11, color: mcColors.textMuted, marginTop: 4 }}>{skill.description}</div>
                    ) : null}
                  </button>
                );
              })}
            </nav>

            <section style={{ ...mcPanelSectionStyle, minHeight: 360 }}>
              {detail ? (
                <>
                  <h2 style={{ margin: "0 0 8px", fontSize: 18 }}>{detail.name || detail.id}</h2>
                  {detail.description ? (
                    <p style={{ margin: "0 0 12px", fontSize: 13, color: mcColors.textMuted }}>{detail.description}</p>
                  ) : null}
                  <pre
                    style={{
                      margin: 0,
                      padding: 14,
                      borderRadius: 10,
                      background: "rgba(0,0,0,0.35)",
                      fontSize: 12,
                      lineHeight: 1.55,
                      whiteSpace: "pre-wrap",
                      overflow: "auto",
                      maxHeight: "55vh",
                      color: mcColors.textMuted,
                    }}
                  >
                    {detail.content || "No content."}
                  </pre>
                  <p style={{ margin: "12px 0 0", fontSize: 11, color: mcColors.textDim }}>
                    In chat (Agent mode): <code>skill_recall {detail.id}</code>
                  </p>
                </>
              ) : (
                <p style={{ margin: 0, color: mcColors.textMuted, fontSize: 13 }}>Select a skill.</p>
              )}
            </section>
          </div>
        ) : null}
      </div>
    </div>
  );
}
